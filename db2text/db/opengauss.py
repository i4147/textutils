import sys, dbcfg
import database2text.tool as dbtt
from database2text.tool import *

字段类型 = {}


class opengauss(object):
    def ana_TABLE(otype):
        for 表id, 表名 in db.exec(
            f"select oid,relname from pg_class where relkind='r' and relnamespace=(select oid from pg_namespace where nspname='{stdata['schema']}') order by oid"
        ):
            odata = db.res1(f"select pg_get_tabledef({表id})")
            oridata = []
            coldata = []
            tdesc = db.res1(f"select description from pg_description where objoid={表id} and objsubid=0")
            md = []
            主键列 = []
            主键名 = db.res1(
                f"select constraint_name from information_schema.table_constraints where table_schema='{stdata['schema']}' and table_name='{表名}' and constraint_type = 'PRIMARY KEY'"
            )
            for (pkcol,) in db.exec(
                f"select column_name from information_schema.key_column_usage where TABLE_SCHEMA='{stdata['schema']}' and table_name='{表名}' and constraint_name='{主键名}'"
            ):
                主键列.append(pkcol)
            for i in db.exec2(
                f"select * from pg_attribute where attrelid={表id} and attnum>0 and not attisdropped order by attnum"
            ):
                oridata.append(i)
                if i["atttypid"] not in 字段类型:
                    字段类型[i["atttypid"]] = db.res1(f"select typname from pg_type where oid={i['atttypid']}")
                mddata = {
                    "name": i["attname"],
                    "type": 字段类型[i["atttypid"]],
                    "size": i["attlen"],
                    "null": not i["attnotnull"],
                    "ts": "",
                }
                mddata["desc"] = db.res1(
                    f"select description from pg_description where objoid={表id} and objsubid={i['attnum']}"
                )
                字符长度, 数字长度, 默认 = db.res1(
                    f"select character_maximum_length,numeric_precision,column_default from information_schema.columns where table_schema='{stdata['schema']}' and table_name='{表名}' and column_name='{i['attname']}'"
                )
                if i["attlen"] < 0:
                    mddata["size"] = 字符长度 or 数字长度
                mddata["default"] = 默认 or ""
                mddata["ts"] = f"{mddata['type']}({mddata['size']})"
                mddata["pk"] = i["attname"] in 主键列
                md.append(mddata)
            dbdata["sql"]["TABLE"][表名] = odata
            dbdata["exp"]["TABLE"].append({"tname": 表名, "tdesc": tdesc, "ori": oridata, "c": coldata, "md": md})

    def getobjtext(otype, oname):
        _, ssql = db.res1("show create %s %s" % (otype, oname))
        return ssql


def readdata(arg):
    dbdata["sql"] = {}
    dbdata["exp"] = {}
    for i in vars(opengauss):
        if i.startswith("ana_"):
            otype = i[4:]
            dbdata["sql"][otype] = {}
            dbdata["exp"][otype] = []
            getattr(opengauss, i)(otype)
    if "schema" not in arg:
        print("读数据必须设置schema")
        sys.exit(1)


def connect(arg):
    if "dbcfg" in stdata:
        db.conn = dbtt.dbc.connect()
    else:
        print("opengauss只支持dbcfg设置连接")
        sys.exit(1)


__all__ = []
