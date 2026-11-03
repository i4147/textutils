import sys, pymysql, dbcfg
import database2text.tool as dbtt
from database2text.tool import *


class mysql(object):
    def ana_TABLE(otype):
        for (oname,) in db.exec(
            f"select table_name from information_schema.tables where table_schema='{database}' and table_type='BASE TABLE' order by 1"
        ):
            if 检查匹配(otype, oname):
                continue
            res = db.res1("show create table %s" % (oname))
            odata = res[1]
            oridata = []
            coldata = []
            tdesc = db.res1(
                "SELECT TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES  WHERE TABLE_NAME ='%s' AND TABLE_SCHEMA = '%s'"
                % (oname, database)
            )
            主键列 = []
            for (pkcol,) in db.exec(
                f"select column_name from information_schema.key_column_usage where TABLE_SCHEMA='{database}' and table_name='{oname}' and constraint_name='PRIMARY'"
            ):
                主键列.append(pkcol)
            md = []
            for i in db.exec2(
                "select * from information_schema.COLUMNS where TABLE_SCHEMA='%s' and table_name='%s' order by ORDINAL_POSITION"
                % (database, oname)
            ):
                oridata.append(i)
                mddata = {
                    "name": i["COLUMN_NAME"],
                    "desc": i["COLUMN_COMMENT"],
                    "type": i["DATA_TYPE"],
                    "size": i["CHARACTER_OCTET_LENGTH"],
                    "null": i["IS_NULLABLE"] == "NO",
                    "default": i["COLUMN_DEFAULT"],
                    "ts": i["COLUMN_TYPE"],
                    "pk": i["COLUMN_NAME"] in 主键列,
                }
                md.append(mddata)
            dbdata["sql"]["TABLE"][oname] = odata
            dbdata["exp"]["TABLE"].append({"tname": oname, "tdesc": tdesc, "ori": oridata, "c": coldata, "md": md})

    def ana_VIEW(otype):
        for (oname,) in db.exec(
            f"select table_name from information_schema.tables where table_schema='{database}' and table_type='VIEW'"
        ):
            if 检查匹配(otype, oname):
                continue
            oridata = []
            coldata = []
            tdesc = db.res1(
                "SELECT TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES  WHERE TABLE_NAME ='%s' AND TABLE_SCHEMA = '%s'"
                % (oname, database)
            )
            md = []
            for i in db.exec2(
                f"select * from information_schema.COLUMNS where TABLE_SCHEMA='{database}' and table_name='{oname}' order by ORDINAL_POSITION"
            ):
                oridata.append(i)
                mddata = {
                    "name": i["COLUMN_NAME"],
                    "desc": i["COLUMN_COMMENT"],
                    "type": i["DATA_TYPE"],
                    "size": i["CHARACTER_OCTET_LENGTH"],
                    "null": i["IS_NULLABLE"] == "NO",
                    "default": i["COLUMN_DEFAULT"],
                    "ts": i["COLUMN_TYPE"],
                }
                md.append(mddata)
            dbdata["exp"]["TABLE"].append({"tname": oname, "tdesc": tdesc, "ori": oridata, "c": coldata, "md": md})

    def getobjtext(otype, oname):
        _, ssql = db.res1("show create %s %s" % (otype, oname))
        return ssql


def readdata(arg):
    dbdata["sql"] = {}
    dbdata["exp"] = {}
    for i in vars(mysql):
        if i.startswith("ana_"):
            otype = i[4:]
            dbdata["sql"][otype] = {}
            dbdata["exp"][otype] = []
            getattr(mysql, i)(otype)


def connect(arg):
    global database
    if "dbcfg" in stdata:
        db.conn = dbtt.dbc.connect()
    else:
        if "port" in stdata:
            stdata["port"] = int(stdata["port"])
        stdata.pop("driver")
        db.conn = pymysql.connect(**stdata)
    database = db.res1("select database()")


__all__ = []
