# -*- coding: utf-8 -*-

import sys
import json
import shutil
import os
import subprocess
import pyperclip

terminal_size = shutil.get_terminal_size()

DELETE = "delete"
SAVE = "store"
LIST = "list"
HELP = "--help"
CMD = "--cmd"
CP = "--cp"
GET = "get"

FILE_NAME = f"{__file__.replace('save.py', '')}save.json"

EXPLAINS = [
    {
        "command": DELETE,
        "explain": "第一引数にdeleteを入力して、第二引数に削除したいidを入力下さい。",
    },
    {
        "command": SAVE,
        "explain": "第一引数にstoreを入力して、第二引数に保存したいテキストを入力下さい。",
    },
    {
        "command": LIST,
        "explain": "第一引数にlistを入力下さい。idと保存されたテキストが表示されます。",
    },
    {
        "command": GET,
        "explain": "第一引数にgetを入力して、第二引数に表示したいテキストのidを入力下さい。",
    },
    {
        "command": CMD,
        "explain": "第三引数に--cmdを入力して、第二引数より前にgetコマンドを入力下さい。",
    },
    {
        "command": CP,
        "explain": "第三引数に--cpを入力して、第二引数より前にgetコマンドを入力下さい。",
    },
    {
        "command": HELP,
        "explain": "コマンドの説明が閲覧できます。",
    },
]


def getSplit():
    split = ""
    for i in range(terminal_size.columns):
        split += "-"
    return split


def main():
    if len(sys.argv) != 1:
        id: int = 0
        data: dict = {"data": []}
        if not os.path.isfile(FILE_NAME):
            with open(FILE_NAME, "w") as f:
                json.dump({}, f, ensure_ascii=False)

        with open(FILE_NAME, mode="rt", encoding="utf-8") as file:
            try:
                data["data"].extend(json.load(file)["data"])
                data_len = len(data["data"])
                if data_len != 0:
                    if "id" in data["data"][data_len - 1]:
                        id = data["data"][data_len - 1]["id"]
            except:
                pass

        if sys.argv[1] == DELETE:
            try:
                for i in range(len(data["data"])):
                    if str(data["data"][i]["id"]) == sys.argv[2]:
                        data["data"].pop(i)
                        break
                with open(FILE_NAME, mode="wt", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
            except:
                print("\033[33mエラーが発生しました。\n引数を確認の上もう一度コマンドを打って下さい。")

        elif sys.argv[1] == SAVE:
            try:
                with open(FILE_NAME, mode="wt", encoding="utf-8") as file:
                    id += 1
                    data["data"].append({
                        "id": id,
                        "content": sys.argv[2],
                    })
                    json.dump(data, file, ensure_ascii=False, indent=2)
            except:
                print("\033[33mエラーが発生しました。\n引数を確認の上もう一度コマンドを打って下さい。")

        elif sys.argv[1] == GET:
            with open(FILE_NAME, mode="rt", encoding="utf-8") as file:
                try:
                    data = json.load(file)["data"]
                    is_find = False
                    for elm in data:
                        if elm["id"] == int(sys.argv[2]):
                            if len(sys.argv) == 4:
                                if sys.argv[3] == CMD:
                                    subprocess.call(elm["content"], shell=True)
                                elif sys.argv[3] == CP:
                                    pyperclip.copy(elm["content"])
                            print(elm["content"])
                            is_find = True
                    if not is_find:
                        print("\033[33midのcontentは見つかりませんでした。")
                except Exception as e:
                    print(e)
                    print("\033[33mエラーが発生しました。\n引数を確認の上もう一度コマンドを打って下さい。")

        elif sys.argv[1] == HELP:
            max = 0
            explains_len = len(EXPLAINS)
            for i in range(explains_len):
                command_len = len(EXPLAINS[i]["command"] if i != explains_len - 1 else "command")
                if max < command_len:
                    max = command_len
            split = getSplit()
            print(split)
            print(f"   {'command'.rjust(max)}     | コマンドの説明")
            print(split)
            for explain in EXPLAINS:
                print(f"   {explain['command'].rjust(max)}     | {explain['explain']}")
            print(split)

        elif sys.argv[1] == LIST:
            with open(FILE_NAME, mode="rt", encoding="utf-8") as file:
                try:
                    data = json.load(file)["data"]
                    split = getSplit()

                    print(split)
                    print(f"|  id  | text")
                    print(split)
                    for elm in data:
                        print(f"|{str(elm['id']).zfill(6)}| {elm['content']}")
                    print(split)
                except:
                    print("\033[33mlistを出力することができませんでした。")
        else:
            print("\033[33m使用することのできないコマンドです。\n--helpでコマンドを確認できます。")
    else:
        print("\033[33m引数を入力下さい。--helpコマンドでコマンドの説明を確認できます。")
