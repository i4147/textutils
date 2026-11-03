import sys, os, difflib, jinja2, re, json, datetime, importlib, pathlib
import db2text as dt
from pprint import pprint

__all__ = ["db", "ckd", "dbdata", "storidata", "stdata", "检查匹配", "cpt"]


def mkdir(dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)


def quit(errinfo, exitcode=0):
    print(errinfo)
    sys.exit(exitcode)


def cpt(t):
    import json

    print(json.dumps(t, ensure_ascii=False, skipkeys=False, indent=2))


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, bytes):
            return ""
        else:
            return json.JSONEncoder.default(self, obj)


class dblib(object):
    def res1(self, ssql, *args, **kwargs):
        c = self.conn.cursor()
        c.execute(ssql, *args, **kwargs)
        res = c.fetchone()
        if res == None:
            return
        if len(res) == 1:
            return res[0]
        else:
            return res

    def exec(self, ssql, *args, **kwargs):
        c = self.conn.cursor()
        c.execute(ssql, *args, **kwargs)
        return c

    def exec2(self, ssql, *args, **kwargs):
        c = self.conn.cursor()
        c.execute(ssql, *args, **kwargs)
        res = []
        col = c.description
        for item in c.fetchall():
            row = {}
            for i in range(len(col)):
                row[col[i][0]] = item[i]
            res.append(row)
        return res


class checkdiff(object):
    def init(self, objtype):
        self.diff = difflib.Differ()
        self.objtype = objtype
        self.datadir = cfgdata["datadir"]
        mkdir(self.datadir)
        self.datadir = "%s/%s" % (self.datadir, objtype)
        mkdir(self.datadir)
        self.filelist = []
        for f in os.listdir(self.datadir):
            self.filelist.append(f)

    def comp(self, objname, objdata):
        fn = "%s/%s" % (self.datadir, objname)
        if os.path.isfile(fn):
            data = open(fn).read()
            if data == objdata:
                return
            print("============diff of %s.%s" % (self.objtype, objname))
            print("\n".join(self.diff.compare(data.split("\n"), objdata.split("\n"))))
        else:
            print("============find new: %s.%s" % (self.objtype, objname))
            print(objdata)
        with open(fn, "w") as f:
            f.write(objdata)


class export(object):
    def __init__(self, arg):
        mkdir(stdata["datadir"])
        for objtype, objdata in dbdata["sql"].items():
            datadir = os.path.join(stdata["datadir"], objtype)
            mkdir(datadir)
            for objname, objdesc in objdata.items():
                self.db2file(datadir, objtype, objname, objdesc)
        for objtype in os.listdir(stdata["datadir"]):
            if objtype not in dbdata["sql"]:
                print(
                    "%s not exists in database,maybe some error fund, check it! if need delete, do it yourself."
                    % (objtype)
                )
                continue
            datadir = os.path.join(stdata["datadir"], objtype)
            for objname in os.listdir(datadir):
                if objname not in dbdata["sql"][objtype]:
                    fn = os.path.join(datadir, objname)
                    print("delete %s !" % (fn))
                    os.unlink(fn)

    def db2file(self, datadir, objtype, objname, objdesc):
        导出文件编码 = stdata.get("code") or stdata.get("coding", "utf8")
        fn = os.path.join(datadir, objname)
        if os.path.isfile(fn):
            data = open(fn, encoding=导出文件编码).read()
            if data == objdesc:
                return
            diff = difflib.Differ()
            print("============ diff of %s.%s" % (objtype, objname))
            print("\n".join(diff.compare(data.split("\n"), objdesc.split("\n"))))
        else:
            print("============ find new: %s.%s" % (objtype, objname))
            print(objdesc)
        with open(fn, "w", encoding=导出文件编码) as f:
            f.write(objdesc)


class dot(object):
    def __init__(self, arg):
        模板文件 = os.path.join(os.path.dirname(os.path.abspath(dt.__file__)), "datafile", "dot.mb")
        模板 = open(模板文件, encoding="utf8").read()
        分页数据 = []
        for page in arg.get("page", "其它").split():
            if page in ["other", "其它", "其他"]:
                if arg.get(page, "输出剩下的所有表") not in 分页数据:
                    分页数据.append(arg.get(page, "输出剩下的所有表"))
            elif page in arg:
                if arg[page] not in 分页数据:
                    分页数据.append(arg[page])
        文件序号 = 0
        已经使用 = set()
        dot列表 = []
        pdf列表 = []
        for 分页 in 分页数据:
            文件序号 = 文件序号 + 1
            dotname = os.path.join(arg.get("dotdir", "."), f"{arg['filename']}_{文件序号}.dot")
            data = {"TABLE": []}
            for t in dbdata["exp"]["TABLE"]:
                if 分页 == "输出剩下的所有表":
                    if t["tname"] not in 已经使用:
                        data["TABLE"].append(t)
                else:
                    if not 检查匹配(分页, t["tname"]):
                        data["TABLE"].append(t)
                        已经使用.add(t["tname"])
            if len(data["TABLE"]) > 0:
                fdot = open(dotname, "wt", encoding="utf8")
                fdot.write(jinja2.Template(模板).render(data))
                fdot.close()
                dot列表.append(dotname)
                pdfname = os.path.join(arg.get("pdfdir", "."), f"{arg['filename']}_{文件序号}.pdf")
                pdf列表.append(pdfname)
                cmd = "%s -Tpdf %s -o %s" % (arg.get("dotcmd", "fdp"), dotname, pdfname)
                print(cmd)
                os.system(cmd)
        if len(pdf列表) > 0:
            import PyPDF3

            pdfout = PyPDF3.PdfFileMerger()
            for i in pdf列表:
                pdf = PyPDF3.PdfFileReader(i)
                pdfout.append(pdf)
            pdfname = os.path.join(arg.get("pdfdir", "."), f"{arg['filename']}.pdf")
            with open(pdfname, "wb") as fout:
                pdfout.write(fout)


class render(object):
    def __init__(self, arg):
        for t in dbdata["exp"]["TABLE"]:
            if not 检查匹配("TABLE", t["tname"]):
                self.rendertable(t)

    def rendertable(self, t):
        if "help" in stdata and stdata["help"].lower() in ["y", "1"]:
            pprint(t)
        tpl = ""
        k = False
        for l in storidata:
            if l.startswith("start="):
                k = True
                continue
            if l.startswith("end="):
                break
            if k:
                tpl = tpl + l
        nt = jinja2.Template(tpl).render(t)
        lnt = nt.split("\n")
        sstart = jinja2.Template(stdata["start"]).render(t)
        send = jinja2.Template(stdata["end"]).render(t)
        if not re.search(sstart, lnt[0]):
            nt = sstart + "\n" + nt
        if not re.search(send, lnt[-1]):
            nt = nt + send
        nt = nt + "\n"
        f = open(stdata["file"], encoding=stdata.get("code") or stdata.get("coding", "utf8"))
        ft = f.readlines()
        newline = f.newlines
        f.close()
        k = False
        ls, le = -1, -1
        ot = ""
        for i in range(len(ft)):
            if ls < 0 and re.search(sstart, ft[i]):
                ls = i
            if ls >= 0 and re.search(send, ft[i]) and (send != "" or ft[i].strip() == ""):
                le = i
                if le > ls:
                    ot = ot + ft[i]
                else:
                    ot = ft[i]
                break
            if ls >= 0:
                ot = ot + ft[i]
        if ot == nt:
            return
        if ot == "":
            ls = len(ft)
        f = open(stdata["file"], "wt", encoding=stdata.get("code") or stdata.get("coding", "utf8"))
        f.newline = newline
        for i in range(len(ft)):
            if i == ls:
                f.write(nt)
            if i < ls or i > le:
                f.write(ft[i])
        if ot == "":
            f.write(nt)
        f.close()


def connect(arg, mname):
    try:
        m = importlib.import_module(mname)
    except:
        print(f"未找到python模块{mname}")
        sys.exit(-1)
    if "dbinfo" in arg:
        dbarg = json.loads(arg["dbinfo"])
        db.conn = m.connect(**dbarg)
        return db.conn


def 检查匹配(类型或者筛选值, 名称):
    if type(名称) != type(""):
        return True
    排除标志 = True
    加减 = "+"
    if 类型或者筛选值.lower() in ["table", "view"]:
        类型或者筛选值 = stdata.get(类型或者筛选值.lower(), "+ .*")
    for i in 类型或者筛选值.split():
        if i in ["+", "-"]:
            加减 = i
        else:
            if re.search("^" + i + "$", 名称, re.I):
                排除标志 = 加减 == "-"
    return 排除标志


class wiki(object):
    def __init__(self, arg):
        import mwclient, dbcfg

        self.arg = arg
        dt.gd.deftitle = arg.get("title", "name:字段名 desc:注释 ts:类型 default:默认值 :说明")
        dbc = dbcfg.use(arg["wiki"])
        cfg = dbc.cfg()
        site = mwclient.Site(cfg["d"]["server"], scheme=cfg["d"]["scheme"], path=cfg["d"]["path"])
        site.login(cfg["d"]["user"], cfg["d"]["password"])
        page = site.pages[arg["page"]]
        if not page.exists:
            quit("未找到wiki页面，请检查配置文件")
        dt.inittext(page.text())
        for t in dbdata["exp"]["TABLE"]:
            if not 检查匹配("TABLE", t["tname"]):
                self.handle_table(t)
        ischanged = False
        if len(dt.gd.text) == len(dt.gd.oritext):
            for i in range(min(len(dt.gd.text), len(dt.gd.oritext))):
                if dt.gd.text[i].strip() != dt.gd.oritext[i].strip():
                    print(f"第{i}行有差异")
                    print(dt.gd.text[i] + ":")
                    print(dt.gd.oritext[i] + ":")
                    ischanged = True
        else:
            print(f"数据有更新,原始数据{len(dt.gd.oritext)}行，更新数据{len(dt.gd.text)}行")
            dt.printdiff(dt.gd.oritext, dt.gd.text)
        if ischanged or len(dt.gd.text) != len(dt.gd.oritext):
            page.edit(dt.gd.linebreak.join(dt.gd.text))

    def handle_table(self, t):
        dt.p(1, t["tname"])
        thead = ['{| class="wikitable"', f"|+ {t['tname']}"]
        ttail = ["|}"]
        dt.capture(thead, ttail)
        dt.analydata()
        mdata = dt.mergecolumndata(t)
        newdata = []
        if dt.gd.capturenothing and "level" in self.arg:
            titlemark = "=" * int(self.arg["level"])
            newdata.append(f"{titlemark} {t['tname']} {t['tdesc']} {titlemark}")
        newdata.append('{| class="wikitable"')
        newdata.append(f"|+ {t['tname']} {t['tdesc']}")
        rowdata = []
        for j in dt.gd.deftitle.split():
            cname, tname = j.split(":")
            rowdata.append(tname)
        newdata.append("|-")
        newdata.append(("! " + " !! ".join(rowdata)).strip())
        for i in dt.createcolumndata(mdata):
            newdata.append("|-")
            newdata.append(("| " + " || ".join(i)).strip())
        newdata.append("|}")
        if dt.gd.capturenothing:
            newdata.append("")
        dt.replacenewdata(newdata)


db = dblib()
ckd = checkdiff()
dbdata = {}
storidata = []
stdata = {}
