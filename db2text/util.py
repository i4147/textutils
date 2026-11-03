__all__ = [
    "inittext",
    "p",
    "capture",
    "mergecolumndata",
    "createcolumndata",
    "replacenewdata",
    "analydata",
    "printdiff",
]
import db2text as dt
import time, copy, difflib
from pprint import pprint


def inittext(text):
    dt.gd.oritext = text.splitlines(False)
    dt.gd.text = text.splitlines(False)
    if text.find("\r\n") >= 0:
        dt.gd.linebreak = "\r\n"
    elif text.find("\r") >= 0:
        dt.gd.linebreak = "\r"


def p(level, fmt, *info):
    if level > dt.gd.infolevel and level != -1:
        return
    if info is None or not info:
        sinfo = time.strftime("%H:%M:%S") + "|%d: " % (level) + fmt
    else:
        sinfo = time.strftime("%H:%M:%S") + "|%d: " % (level) + fmt % (info)
    if level >= 0:
        print(sinfo)
    else:
        sys.stderr.write(sinfo + "\n")


def capture(thead, ttail):
    dt.gd.capturenothing = False
    for i in range(len(dt.gd.text) - len(thead) - len(ttail)):
        for j in range(len(thead)):
            if not dt.gd.text[i + j].startswith(thead[j]):
                break
        else:
            for j in range(i + len(thead) + 1, len(dt.gd.text) - len(ttail) + 1):
                for k in range(len(ttail)):
                    if not dt.gd.text[j + k].startswith(ttail[k]):
                        break
                else:
                    dt.gd.capturebegin = i
                    dt.gd.captureend = j + len(ttail) - 1
                    return
    dt.gd.capturebegin = len(dt.gd.text)
    dt.gd.captureend = len(dt.gd.text)
    dt.gd.capturenothing = True


def analydata():
    dt.gd.capturedata = {}
    if dt.gd.capturenothing:
        return
    oldtitle = []
    for i in range(dt.gd.capturebegin, dt.gd.captureend):
        if (dt.gd.text[i].startswith("|") and dt.gd.text[i].endswith("|")) or dt.gd.text[i][0] == "!":
            oldtitle = dt.gd.text[i].replace("!", "|").replace("||", "|").split("|")
            oldtitle = oldtitle[1:]
            break
    if len(oldtitle) == 0:
        return
    columnname = ""
    for j in dt.gd.deftitle.split():
        cname, tname = j.split(":")
        if cname == "name":
            columnname = tname
            break
    if not columnname:
        return
    titlecount = len(oldtitle)
    keynum = -1
    for i in range(len(oldtitle)):
        if oldtitle[i].strip() == columnname:
            keynum = i
            break
    if keynum == -1:
        return
    for i in range(dt.gd.capturebegin, dt.gd.captureend):
        t = dt.gd.text[i].replace("!", "|").replace("||", "|").split("|")
        if len(t) < titlecount + 1:
            continue
        t = t[1:]
        dt.gd.capturedata[t[keynum].strip()] = {}
        for j in range(len(oldtitle)):
            dt.gd.capturedata[t[keynum].strip()][oldtitle[j].strip()] = t[j].strip()


def mergecolumndata(t):
    retdata = []
    for i in t["md"]:
        rowdata = copy.deepcopy(dt.gd.capturedata.get(i["name"], {}))
        retdata.append(rowdata | i)
    return retdata


def createcolumndata(mdata):
    retdata = []
    for i in mdata:
        rowdata = []
        for j in dt.gd.deftitle.split():
            cname, tname = j.split(":")
            rowdata.append(i.get(cname, i.get(tname, "")) or "")
        retdata.append(rowdata)
    return retdata


def replacenewdata(newdata):
    dt.gd.text = dt.gd.text[: dt.gd.capturebegin] + newdata + dt.gd.text[dt.gd.captureend + 1 :]


def printdiff(t1, t2):
    diff = difflib.Differ()
    print("\n".join(difflib.context_diff(t1, t2)))
