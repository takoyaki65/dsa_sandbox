import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="path to the database")
    parser.add_argument(
        "test_type", choices=["light", "heavy", "all"], help="Type of test cases to run"
    )
    parser.add_argument("assignment_id", help="ID of the assignment")
    parser.add_argument(
        "submitted_codes", nargs="+", help="Paths to the submitted code files"
    )
    args = parser.parse_args()

    with sqlite3.connect(args.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assignment WHERE id = ?", (args.assignment_id,))
        row = cursor.fetchone()
        if row is None:
            print("Assignment not found")
            return

    assignment = {
        "id": row[0],
        "max_time": row[1],
        "max_memory": row[2],
        "required_files": json.loads(row[3]),
        "test_codes": json.loads(row[4]),
        "makefile": row[5],
        "compile_command": row[6],
        "binary_name": row[7],
        "light_test_cases": json.loads(row[8]),
        "heavy_test_cases": json.loads(row[9]),
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        for filename, content in assignment["test_codes"].items():
            with open(os.path.join(temp_dir, filename), "w", encoding="utf8") as f:
                f.write(content)

        with open(os.path.join(temp_dir, "Makefile"), "w", encoding="utf8") as f:
            f.write(assignment["makefile"])

        test_cases = []
        if args.test_type in ["light", "all"]:
            test_cases.extend(assignment["light_test_cases"])
        if args.test_type in ["heavy", "all"]:
            test_cases.extend(assignment["heavy_test_cases"])

        for test_case in test_cases:
            with open(
                os.path.join(temp_dir, f"{test_case['name']}.in"), "w", encoding="utf8"
            ) as f:
                f.write(test_case["in"])
            with open(
                os.path.join(temp_dir, f"{test_case['name']}.exp"), "w", encoding="utf8"
            ) as f:
                f.write(test_case["out"])

        for submitted_code in args.submitted_codes:
            shutil.copy(submitted_code, temp_dir)

        container_name = f"dsa_sandbox_{uuid.uuid4()}"
        subprocess.run(
            [
                "docker",
                "run",
                "-td",
                "--security-opt",
                "no-new-privileges",
                "--name",
                container_name,
                "--memory",
                f"{assignment['max_memory']}k",
                "--network",
                "none",
                "-v",
                f"{temp_dir}:/home/user",
                "dsa_sandbox",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        
        result={
            "status": "AC",
            "max_time": 0,
            "max_memory": 0,
            "compile_log": "",
            "detail": [],
        }

        
        compile_log_file = os.path.join(temp_dir, "compile.log")
        with open(compile_log_file, "w", encoding="utf8") as f:
            result_compile = subprocess.run(
                [
                    "docker",
                    "exec",
                    container_name,
                    "sh",
                    "-c",
                    f"timeout 30 {assignment['compile_command']}",
                ],
                check=True,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )

        result["compile_log"] = open(compile_log_file, "r", encoding='utf8').read()

        if result_compile.returncode != 0:
            result["status"] = "CE"
            print(json.dumps(result))
            subprocess.run(["docker", "rm", "-f", container_name], check=True)
            return
        
        if not os.path.exists(os.path.join(temp_dir, assignment["binary_name"])):
            result["status"] = "CE"
            print(json.dumps(result))
            subprocess.run(["docker", "rm", "-f", container_name], check=True)
            return

        for test_case in test_cases:
            test_log_file = os.path.join(temp_dir, f"{test_case['name']}.log")
            with open(test_log_file, "w", encoding='utf8') as f:
                result_run = subprocess.run(
                    [
                        "docker",
                        "exec",
                        container_name,
                        "sh",
                        "-c",
                        f"timeout {assignment['max_time'] / 1000} "
                        f"time -f '%e %M' "
                        f"./{assignment['binary_name']} < {test_case['name']}.in > {test_case['name']}.out",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=f,
                    text=True,
                    check=True,
                )

            if result_run.returncode == 124:
                result["status"] = "TLE"
                result["detail"].append(
                    {
                        "name": test_case["name"],
                        "status": "TLE",
                        "time": assignment["max_time"],
                        "memory": 0,
                        "input": test_case["in"],
                        "output": "",
                        "expect": test_case["out"],
                    }
                )
            elif result_run.returncode != 0:
                result["status"] = "RE"
                result["detail"].append(
                    {
                        "name": test_case["name"],
                        "status": "RE",
                        "time": 0,
                        "memory": 0,
                        "input": test_case["in"],
                        "output": "",
                        "expect": test_case["out"],
                    }
                )
            else:
                # print("stdout", result_run.stdout)
                # print("stderr", open(test_log_file, "r", encoding='utf8').read())
                time_memory = open(test_log_file, "r", encoding='utf8').read().split()
                time_sec = float(time_memory[0])
                memory_kb = int(time_memory[1])

                with open(os.path.join(temp_dir, f"{test_case['name']}.out"), "r", encoding='utf8') as f:
                    output = f.read()
                
                with open(os.path.join(temp_dir, f"{test_case['name']}.exp"), "r", encoding='utf8') as f:
                    expect = f.read()
                
                if output.strip() == expect.strip():
                    result["detail"].append(
                        {
                            "name": test_case["name"],
                            "status": "AC",
                            "time": time_sec,
                            "memory": memory_kb,
                            "input": test_case["in"],
                            "output": output,
                            "expect": expect,
                        }
                    )
                else:
                    result["status"] = "WA"
                    result["detail"].append(
                        {
                            "name": test_case["name"],
                            "status": "WA",
                            "time": time_sec,
                            "memory": memory_kb,
                            "input": test_case["in"],
                            "output": output,
                            "expect": expect,
                        }
                    )
        
        subprocess.run(["docker", "rm", "-f", container_name], check=True)
    
    result["max_time"] = max([test["time"] for test in result["detail"]])
    result["max_memory"] = max([test["memory"] for test in result["detail"]])

    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()
