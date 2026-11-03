import sys, cx_Oracle, json
import database2text.tool as dbtt
from database2text.tool import *


class oracle(object):
    def ana_TABLE(otype):
        for (oname,) in db.exec(
            "select object_name from all_objects where object_type=:ot and owner=:owner order by 1",
            ot=otype,
            owner=owner,
        ):
            if 检查匹配(otype, oname):
                continue
            if oname.startswith("SYS_EXPORT_TABLE"):
                continue
            odata = "create table %s\n(\n" % (oname)
            coldata = []
            md = []
            maxcsize = db.res1(
                "select max(length(column_name)) from all_tab_cols where owner='%s' and table_name='%s'"
                % (owner, oname)
            )
            tdesc = db.res1("select comments from all_tab_comments where owner=:1 and table_name=:2", [owner, oname])
            if not tdesc:
                tdesc = ""
            oridata = []
            for col in db.exec2(
                "select * from all_tab_cols where owner='%s' and table_name='%s' order by column_id" % (owner, oname)
            ):
                col["COLUMN_COMMENT"] = db.res1(
                    "select comments from all_col_comments where table_name=:1 and column_name=:2 and owner=:3",
                    [oname, col["COLUMN_NAME"], owner],
                )
                if col["DATA_DEFAULT"] != None:
                    col["DATA_DEFAULT"] = col["DATA_DEFAULT"].strip()
                oridata.append(col)
            for (
                column_name,
                data_type,
                char_length,
                data_precision,
                data_scale,
                nullable,
                default_length,
                data_default,
            ) in db.exec(
                "select column_name,data_type,char_length,data_precision,data_scale,nullable,default_length,data_default from all_tab_cols where owner='%s' and table_name='%s' order by column_id"
                % (owner, oname)
            ):
                if data_default:
                    data_default = data_default.strip()
                odata = odata + "  %s%*s" % (column_name, maxcsize - len(column_name) + 1, " ")
                ctype = "char"
                desc = db.res1(
                    "select comments from all_col_comments where table_name=:1 and column_name=:2 and owner=:3",
                    [oname, column_name, owner],
                )
                if not desc:
                    desc = ""
                if data_type == "NUMBER":
                    if data_precision is not None and data_scale is not None:
                        if data_scale == 0:
                            if data_precision < 8:
                                ctype = "int"
                            else:
                                ctype = "long"
                            odata = odata + "NUMBER(%d)" % (data_precision)
                            ts = f"NUMBER({data_precision})"
                        else:
                            ctype = "double"
                            odata = odata + "NUMBER(%d,%d)" % (data_precision, data_scale)
                            ts = f"NUMBER({data_precision}.{data_scale})"
                    elif data_precision is None and data_scale == 0:
                        ctype = "long"
                        odata = odata + "INTEGER"
                        ts = "INTEGER"
                    elif char_length == 0:
                        ctype = "long"
                        odata = odata + "NUMBER"
                        ts = "INTEGER"
                    else:
                        print(
                            "table %s column %s type %s length %s %s %s"
                            % (oname, column_name, data_type, char_length, data_precision, data_scale)
                        )
                        sys.exit(-1)
                    cns = column_name
                elif data_type in ("VARCHAR2", "VARCHAR", "CHAR", "NVARCHAR2", "NVARCHAR"):
                    if char_length == 1:
                        ts = data_type
                    else:
                        ts = f"{data_type}({char_length})"
                    cns = "%s[%d]" % (column_name, char_length + 1)
                    odata = odata + "%s(%d)" % (data_type, char_length)
                elif data_type.startswith("TIMESTAMP"):
                    cns = "%s[20]" % (column_name)
                    odata = odata + "%s" % (data_type)
                    ts = data_type
                elif data_type in ("DATE"):
                    cns = "%s[20]" % (column_name)
                    odata = odata + "%s" % (data_type)
                    ts = data_type
                elif data_type in ("CLOB", "BLOB", "NCLOB", "LONG", "RAW"):
                    cns = "%s[2000]" % (column_name)
                    odata = odata + "%s" % (data_type)
                    ts = data_type
                elif data_type in ("FLOAT"):
                    ctype = "double"
                    odata = odata + "FLOAT(%d)" % (data_precision)
                    ts = data_type
                elif data_type in ("ROWID"):
                    cns = "%s[100]" % (column_name)
                    odata = odata + "%s" % (data_type)
                    ts = data_type
                else:
                    print(
                        "table %s column %s type %s length %s %s %s"
                        % (oname, column_name, data_type, char_length, data_precision, data_scale)
                    )
                    sys.exit(-1)
                if default_length:
                    odata = odata + " default %s" % (data_default)
                if nullable == "N":
                    odata = odata + " not null"
                odata = odata + ",\n"
                cns2 = cns
                if data_type in ("VARCHAR2", "VARCHAR", "CHAR", "NVARCHAR2", "NVARCHAR") and char_length == 1:
                    cns = column_name
                coldata.append({"type": ctype, "name": column_name, "ns": cns, "ns2": cns2, "desc": desc})
                主键列 = []
                for (pkcol,) in db.exec(
                    f"SELECT cols.column_name FROM user_constraints cons, user_cons_columns cols WHERE cons.constraint_type = 'P' AND cons.constraint_name = cols.constraint_name AND cons.owner = cols.owner and cons.owner = '{owner}' AND cols.table_name = '{oname}'"
                ):
                    主键列.append(pkcol)
                md.append({
                    "name": column_name,
                    "desc": desc,
                    "type": data_type,
                    "size": char_length,
                    "null": nullable == "N",
                    "default": data_default,
                    "ts": ts,
                    "pk": column_name in 主键列,
                })
            odata = odata[:-2]
            odata = odata + "\n);"
            dbdata["sql"]["TABLE"][oname] = odata
            dbdata["exp"]["TABLE"].append({"tname": oname, "tdesc": tdesc, "ori": oridata, "c": coldata, "md": md})

    def ana_VIEW(otype):
        for (oname,) in db.exec("select object_name from user_objects where object_type=:ot", ot=otype):
            if "view" in stdata and oname.lower() not in stdata["view"].split() and oname not in stdata["view"].split():
                continue
            dbdata["sql"][otype][oname] = oracle.getobjtext(otype, oname)

    def getobjtext(otype, oname):
        c = db.conn.cursor()
        try:
            c.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", (-1, "TABLESPACE", False))
            c.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", (-1, "STORAGE", False))
            c.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", (-1, "SEGMENT_ATTRIBUTES", False))
            c.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", (-1, "PRETTY", False))
        except:
            pass
        ssql = db.res1("SELECT dbms_metadata.get_ddl(:otype,:oname) FROM DUAL", otype=otype, oname=oname).read()
        return ssql


def readdata(arg):
    global owner
    dbdata["sql"] = {}
    dbdata["exp"] = {}
    if "owner" in arg:
        owner = arg["owner"]
    for i in vars(oracle):
        if i.startswith("ana_"):
            otype = i[4:]
            dbdata["sql"][otype] = {}
            dbdata["exp"][otype] = []
            getattr(oracle, i)(otype)


def connect(arg):
    global owner
    if "dbcfg" in stdata:
        db.conn = dbtt.dbc.connect()
    else:
        db.conn = cx_Oracle.connect(stdata["loginname"], stdata["password"], stdata["dbserver"])
    if "owner" in stdata:
        owner = stdata["owner"]
    else:
        owner = db.res1("select user from dual")


__all__ = []
