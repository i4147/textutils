import click
from lark import Lark
from .pipeline import pipeline_raw, string_to_pipeline, tree_to_pipeline
from ..textlefile import Textle

l = Lark(
    """
%import common.WS
%ignore WS
%ignore /^#.*$/m

%import common.ESCAPED_STRING
%import common.CNAME
%import common.LETTER
%import common.NUMBER

ONAME: (LETTER|"_"|"-") (LETTER|NUMBER|"_"|"-")*

BOOLEAN: "true" | "false"
DEFAULT: "default"

?value: NUMBER
      | ESCAPED_STRING
      | BOOLEAN
      | DEFAULT

textlefile: version_decl options ("---" pipeline_i)+

?version_decl: "version" NUMBER
options: (ONAME "=" value)*

pipeline_i: pipeline (section options)*

?section: "[" CNAME "]"
"""
    + pipeline_raw,
    start="textlefile",
)
VERSION = 1


def textlefile_from_string(string, root):
    return textlefile_from_tree(l.parse(string), root)


def _create_odict(options):
    odict = {}
    for name, val in zip(options.children[::2], options.children[1::2]):
        n = name.value
        if val.type == "NUMBER":
            v = int(val.value)
        elif val.type == "ESCAPED_STRING":
            v = val.value[1:-1]
        elif val.type == "BOOLEAN":
            v = True if val.value == "true" else False
        else:
            continue
        if n in odict and type(odict[n]) == list:
            odict[n].append(v)
        elif n in odict:
            odict[n] = [odict[n], v]
        else:
            odict[n] = v
    return odict


def textlefile_from_tree(tree, root):
    glob_options = _create_odict(tree.children[1])
    pipelines = []
    for pipeline_i in tree.children[2:]:
        intern_opts = {}
        for section, opt in zip(pipeline_i.children[1::2], pipeline_i.children[2::2]):
            intern_opts[section.value] = _create_odict(opt)
        pipelines.append(tree_to_pipeline(pipeline_i.children[0], intern_opts))
    return Textle(pipelines, glob_options, root)


def _odict_to_string(odict):
    def _value_out(c):
        if type(c) is int:
            return str(c)
        elif type(c) is str:
            return '"{}"'.format(c.replace('"', '\\"'))
        else:
            return str(c).lower()

    for k, v in odict.items():
        if type(v) is not list:
            yield "{}={}".format(k, _value_out(v))
        else:
            for i in v:
                yield "{}={}".format(k, _value_out(i))


def create_textlefile_string_from(pipelines, glob_options, glob_sections):
    for i in pipelines:
        try:
            g = string_to_pipeline(i, glob_sections)
        except:
            click.echo("Pipeline is invalid: {}".format(i), err=True)
            raise
    output = "version {}\n\n".format(VERSION)
    output += "\n".join(_odict_to_string(glob_options)) + "\n\n"
    for i in pipelines:
        output += "---\n"
        output += i + "\n\n"
        for sect, d in glob_sections.items():
            output += "[{}]\n\n".format(sect)
            output += "\n".join(_odict_to_string(d)) + "\n\n"
    return output
