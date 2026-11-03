import sys, importlib, os, shutil, dbcfg
import db2text.tool as dbtt
from db2text.tool import *
import db2text as dt


def 读文件():
    rd = []
    fn = "dbt.txt"
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    if not os.path.isfile(fn):
        print(f"无法打开文件{fn}. 你可以生成一个模块文件或者在命令行指定一个模板文件")
        print(
            "可以在目录%s下查看帮助和模板文件样例"
            % (os.path.join(os.path.dirname(os.path.abspath(dt.__file__)), "datafile"))
        )
        sys.exit(-1)
    f = open(fn, "rb")
    if fn.endswith("md"):
        配置区域 = False
        for s in f.readlines():
            if s.decode("latin1").startswith("-->"):
                配置区域 = False
            if 配置区域:
                rd.append(s)
            if s.decode("latin1").startswith("<!-- dbt"):
                配置区域 = True
    else:
        rd = f.readlines()
    f.close()
    return rd


def main():
    驱动表 = {"oracle": "oracle11", "tds": "mssql"}
    section = "global"
    文件编码 = "utf8"
    dbt = ""
    for s in 读文件():
        s = s.decode(文件编码)
        if s.startswith(":"):
            if section == "end":
                break
            if section == "global":
                文件编码 = stdata.get("code") or stdata.get("coding") or 文件编码
            if section in ["connect", "global"] and "driver" in stdata:
                dbt = importlib.import_module("db2text.db.%s" % (stdata["driver"]))
            if section == "connect" and "dbcfg" in stdata:
                dbtt.dbc = dbcfg.use(stdata["dbcfg"], ehm=2)
                dbtt.cfg = dbtt.dbc.cfg()
                if "driver" not in stdata:
                    dbt = importlib.import_module("db2text.db.%s" % (驱动表.get(dbtt.cfg["db"], dbtt.cfg["db"])))
            if section != "global":
                if not dbt:
                    print("需要在配置文件里设置driver")
                    sys.exit(-1)
                if hasattr(dbt, section):
                    getattr(dbt, section)(stdata)
                elif hasattr(dbtt, section):
                    getattr(dbtt, section)(stdata)
                else:
                    print(f"在配置文件中发现未知的节{section},请检查格式是否正确")
                    sys.exit(-2)
            section = s[1:].strip()
            storidata.clear()
            stdata.clear()
            continue
        storidata.append(s)
        s = s.rstrip()
        if s.find("=") >= 0:
            name = s[: s.find("=")].strip()
            value = s[s.find("=") + 1 :].strip()
            if name in stdata and stdata[name][-1:] == "\\":
                stdata[name] = stdata[name][:-1] + value
            else:
                stdata[name] = value


if __name__ == "__main__":
    main()
