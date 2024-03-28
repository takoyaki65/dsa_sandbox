以下のように、最大公約数を求めるC言語関数をユーザが作成するとする。

ファイル名: gcd_euclid.c
```
int gcd_euclid(int a, int b) {
  while (b != 0) {
    int t = a % b;
    a = b;
    b = t;
  }
  return a;
}

```


この関数が正しいかチェックするようなシステムを作成したい。

システム側では、ユーザが提供したgcd_euclid.cと、システム側が持っているテストプログラムmain_euclid.cをリンクして実行ファイルを生成し、システム側で持っている入力ファイルを用いてプログラムに入力し、出力結果が正解ファイルと合っているかチェックする．

ファイル名: main_euclid.c
```
#include <stdio.h>

int gcd_euclid(int, int);

int main(int argc, char **argv) {
  int a, b;
  scanf("%d %d", &a, &b);  
  printf("%d\n", gcd_euclid(a, b));
  return 0;
}

```

ビルドファイル名: Makefile
```
gcd_euclid: gcd_euclid.o main_euclid.o
```

入力ファイル名: sample00.in
```
15 30

```

正解ファイル名: sample00.out
```
15

```

この課題はID"1-1"の課題で、Makefileの内容やら入出力データの情報はすべてsqlite3データベースである"db.sqlite3"ファイルで、assignmentテーブルに格納している。

* id: 課題のID
* max_time: 各テストケースの最大実行時間(ms)
* max_memory: 実行するコンテナの最大メモリ消費量(kB)
* required_files: ユーザが提出を求められているファイル名(JSON array)
* test_codes: テストプログラムのソースコード(JSON dict)
* makefile: Makefileの内容
* compile_command: ビルドする際のコマンド
* binary_name: ビルドして得られる実行ファイル
* light_test_cases: サンプルケース(JSON array)
* heavy_test_cases: より厳しいテストケース(JSON array)

```
sqlite> .header ON
sqlite> select * from assignment;
id|max_time|max_memory|required_files|test_codes|makefile|compile_command|binary_name|light_test_cases|heavy_test_cases
1-1|2000|262144|["gcd_euclid.c"]|{"main_euclid.c": "#include <stdio.h>\n\nint gcd_euclid(int, int);\n\nint main(int argc, char **argv) {\n  int a, b;\n  scanf(\"%d %d\", &a, &b);  \n  printf(\"%d\\n\", gcd_euclid(a, b));\n  return 0;\n}\n"}|gcd_euclid: gcd_euclid.o main_euclid.o
|make|gcd_euclid|[{"name": "sample00", "in": "15 30\n", "out": "15\n"}, {"name": "sample01", "in": "461952 116298\n", "out": "18\n"}]|[{"name": "test00", "in": "7966496 314080416", "out": "32\n"}, {"name": "test01", "in": "24826148 45296490\n", "out": "526\n"}]

```

システムの出力は、以下が記されたJSONファイル`log.json`である。

status: AC(アクセプト)/WA(出力が違う)/RE(実行時エラー)/TLE(制限時間超過)/CE(コンパイルエラー)
time: ～ms
memory: ～kB
compile log: WarningやErrorやらのログ
各ケース毎の、実行結果: (ケース名、結果、実行時間、メモリ)

```
{
  "status": "WA",
  "max_time": 1341,
  "max_memory": 345,
  "compile_log": "Warning: xxx~",
  "detail": [
    {"name": "sample00", "time":123, "memory": 312, "input": "1 2\n", "output": "3\n", "expect": "4\n"},
    {"name": "sample01", "time":1341, "memory": 345, "input": "3 4\n", "output": "7\n", "expect": "7\n"}
  ]
}
```

なお、テストプログラムのコンパイルには、実行時間を設けるが、これは厳密に計測しないしそこまで厳密でなくてもよい。またプログラムの実行の際には、実行結果にRE(実行時エラー)やTLE(制限時間超過)があるように、実行時間を制限したい。メモリ使用量は厳密に制限するのが難しいので、dockerコンテナを立ち上げる際のオプションで--memory="50m"といったように指定する。実行時間の制限はtimeoutコマンドで、実行時間の計測はtimeコマンドで行いたい。

ユーザが提出したgcd_iter.cには悪意のあるコードが含まれているかもしれない。そのため、テストプログラムの実行時には、ネットワーク通信を禁止したい。また、リクエストの度にフレッシュなコンテナを使用し、使い終わったら破棄する。

コンテナイメージは、以下のDockerファイルを用いてビルドした`dsa_sandbox`を用いる。gcc(+stdlibcライブラリ)とmakeが使える。

ファイル名: Dockerfile
```
FROM alpine:latest

RUN apk update && \
    apk add --no-cache make gcc musl-dev

ENV HOME /home/user
RUN mkdir -p ${HOME}
WORKDIR ${HOME}

```

ホスト側では、`judge.py`というpythonスクリプトを用いて、以下のようにジャッジを行う。

```
$ python3 judge.py /path/to/db [light|heavy|all] assignment_id /path/to/submitted_code0, path/to/submitted_code1, ...
```

このスクリプトでは、tempfileモジュールを用いて一時的なフォルダを作り、そこにデータベースから問題IDに該当するテストコード、(main_euclid.c)、Makefile、入出力ケースファイル(sample00.in, sample00.out,...)を書き込む。そのあとユーザが提出したコードも書き込む。最後に、dsa_sandboxイメージからコンテナを立ち上げ、その際コンテナの`/home/user`ディレクトリに先ほど作成した一時フォルダをリンクさせる。立ち上げたコンテナ上で、`timeout`コマンドによる制限時間付き(一律30秒)でビルドし、`timeout`コマンドによる制限時間付きで各テストケースを実行し、結果が一致するか確認する。この時、`time`コマンドで実行時間とメモリ消費量も確認する。得られた結果をJSONにまとめ、コンテナを削除し、結果のJSONを標準出力して終わる。

