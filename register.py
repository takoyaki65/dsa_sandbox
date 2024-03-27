import json
import sys
import sqlite3
import os

if len(sys.argv) < 3:
    print("Usage: python register.py <db_path> <assignment_dir>")
    sys.exit(1)

db_path = os.path.abspath(sys.argv[1])
assignment_dir = os.path.abspath(sys.argv[2])

if not os.path.exists(assignment_dir):
    print("Error: directory does not exist")
    sys.exit(1)

settings_json_path = os.path.join(assignment_dir, "settings.json")
if not os.path.exists(settings_json_path):
    print("Error: settings.json does not exist")
    sys.exit(1)

# connect ./db.sqlite3
conn = sqlite3.connect(db_path)
c = conn.cursor()

# read setting.json
with open(settings_json_path, "r", encoding="utf8") as f:
    settings = json.load(f)

assignment_id: str = settings["id"]
max_time: int = settings["max_time"]  # ms
max_memory: int = settings["max_memory"]  # kB
required_files: list[str] = settings["required_files"]
test_code_names: list[str] = settings["test_codes"]
test_codes: dict[str, str] = {}

for test_code_name in test_code_names:
    test_code_path = os.path.join(assignment_dir, test_code_name)
    with open(test_code_path, "r", encoding="utf8") as f:
        test_code = f.read()
    test_codes[test_code_name] = test_code

makefile_path: str = os.path.join(assignment_dir, settings["makefile"])
makefile: str = ""
with open(makefile_path, "r", encoding="utf8") as f:
    makefile = f.read()
compile_command: str = settings["compile_command"]
binary_file: str = settings["binary_file"]

light_test_cases_names: list[str] = settings["light_test_cases"]
light_test_cases: list[dict[str, str]] = []
for test_case_name in light_test_cases_names:
    input_path = os.path.join(assignment_dir, test_case_name + ".in")
    output_path = os.path.join(assignment_dir, test_case_name + ".out")
    with open(input_path, "r", encoding="utf8") as f:
        input_data = f.read()
    with open(output_path, "r", encoding="utf8") as f:
        output_data = f.read()
    light_test_cases.append(
        {"name": test_case_name, "in": input_data, "out": output_data}
    )

heavy_test_cases_names: list[str] = settings["heavy_test_cases"]
heavy_test_cases: list[dict[str, str]] = []
for test_case_name in heavy_test_cases_names:
    input_path = os.path.join(assignment_dir, test_case_name + ".in")
    output_path = os.path.join(assignment_dir, test_case_name + ".out")
    with open(input_path, "r", encoding="utf8") as f:
        input_data = f.read()
    with open(output_path, "r", encoding="utf8") as f:
        output_data = f.read()
    heavy_test_cases.append(
        {"name": test_case_name, "in": input_data, "out": output_data}
    )

# insert assignment table
# TABLE assignment(id TEXT PRIMARY KEY, max_time INTEGER, max_memory INTEGER, required_files TEXT, makefile TEXT, compile_command TEXT, binary_name TEXT, light_test_cases TEXT, heavy_test_cases TEXT)
# required_files, light_test_cases, heavy_test_cases are json string
c.execute(
    "INSERT OR REPLACE INTO assignment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (
        assignment_id,
        max_time,
        max_memory,
        json.dumps(required_files),
        json.dumps(test_codes),
        makefile,
        compile_command,
        binary_file,
        json.dumps(light_test_cases),
        json.dumps(heavy_test_cases),
    ),
)

conn.commit()
conn.close()
