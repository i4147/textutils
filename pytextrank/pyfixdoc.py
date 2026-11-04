# -*- coding: utf-8 -*-


from icecream import ic
import inspect
import os
import re
import sys
import traceback
import typing


class PackageDoc:
    PAT_PARAM = re.compile(r"(    \S+.*\:\n(?:\S.*\n)+)", re.MULTILINE)
    PAT_NAME = re.compile(r"^\s+(.*)\:\n(.*)")
    PAT_FWD_REF = re.compile(r"ForwardRef\('(.*)'\)")

    def __init__(
        self,
        module_name: str,
        git_url: str,
        class_list: typing.List[str],
    ) -> None:
        self.module_name = module_name
        self.git_url = git_url
        self.class_list = class_list

        self.module_obj = sys.modules[self.module_name]
        self.md: typing.List[str] = ["# Reference: `{}` package".format(self.module_name)]

    def show_all_elements(self) -> None:
        for name, obj in inspect.getmembers(self.module_obj):
            for n, o in inspect.getmembers(obj):
                ic(name, n, o)
                ic(type(o))

    def write_markdown(
        self,
        path: str,
    ) -> None:
        ic("writing", path)

        with open(path, "w") as f:
            for line in self.md:
                f.write(line)
                f.write("\n")

    def build(self) -> None:
        todo_list: typing.Dict[str, typing.Any] = self.get_todo_list()

        self.md.extend(self.get_docstring(self.module_obj))

        for class_name in self.class_list:
            self.format_class(todo_list, class_name)

        self.format_functions()
        self.format_types()

    def get_todo_list(self) -> typing.Dict[str, typing.Any]:
        todo_list: typing.Dict[str, typing.Any] = {
            class_name: class_obj
            for class_name, class_obj in inspect.getmembers(self.module_obj, inspect.isclass)
            if class_name in self.class_list
        }

        return todo_list

    def get_docstring(
        self,
        obj,
        parse=False,
        arg_dict: dict = None,
    ) -> typing.List[str]:
        if arg_dict is None:
            arg_dict = {}

        local_md: typing.List[str] = []
        raw_docstring = obj.__doc__

        if raw_docstring:
            docstring = inspect.cleandoc(raw_docstring)

            if parse:
                local_md.append(self.parse_method_docstring(docstring, arg_dict))
            else:
                local_md.append(docstring)

            local_md.append("\n")

        return local_md

    def parse_method_docstring(
        self,
        docstring: str,
        arg_dict: dict,
    ) -> str:
        local_md: typing.List[str] = []

        for chunk in self.PAT_PARAM.split(docstring):
            m_param = self.PAT_PARAM.match(chunk)

            if m_param:
                param = m_param.group()
                m_name = self.PAT_NAME.match(param)

                if m_name:
                    name = m_name.group(1).strip()
                    anno = self.fix_fwd_refs(arg_dict[name])
                    descrip = m_name.group(2).strip()

                    if name == "returns":
                        local_md.append("\n  * *{}* : `{}`  \n{}".format(name, anno, descrip))
                    elif name == "yields":
                        local_md.append("\n  * *{}* :  \n{}".format(name, descrip))
                    else:
                        local_md.append("\n  * `{}` : `{}`  \n{}".format(name, anno, descrip))
            else:
                chunk = chunk.strip()

                if len(chunk) > 0:
                    local_md.append(chunk)

        return "\n".join(local_md)

    def fix_fwd_refs(
        self,
        anno: str,
    ) -> typing.Optional[str]:
        results: list = []

        if not anno:
            return None
        for term in anno.split(", "):
            for chunk in self.PAT_FWD_REF.split(term):
                if len(chunk) > 0:
                    results.append(chunk)

        return ", ".join(results)

    def document_method(
        self,
        path_list: list,
        name: str,
        obj: typing.Any,
        func_kind: str,
    ) -> typing.Tuple[int, typing.List[str]]:
        local_md: typing.List[str] = ["---"]

        frag = ".".join(path_list + [name])
        anchor = "#### [`{}` {}](#{})".format(name, func_kind, frag)
        local_md.append(anchor)

        code = obj.__code__
        line_num = code.co_firstlineno
        file = code.co_filename.replace(os.getcwd(), "")

        src_url = "[*\[source\]*]({}{}#L{})\n".format(self.git_url, file, line_num)
        local_md.append(src_url)

        sig = inspect.signature(obj)
        arg_list = self.get_arg_list(sig)
        arg_list_str = "{}".format(", ".join([a[0] for a in arg_list]))

        local_md.append("```python")
        local_md.append("{}({})".format(name, arg_list_str))
        local_md.append("```")

        arg_dict: dict = {name.split("=")[0]: anno for name, anno in arg_list}

        arg_dict["yields"] = None

        ret = sig.return_annotation

        if ret:
            arg_dict["returns"] = self.extract_type_annotation(ret)

        local_md.extend(self.get_docstring(obj, parse=True, arg_dict=arg_dict))
        local_md.append("")

        return line_num, local_md

    def get_arg_list(
        self,
        sig: inspect.Signature,
    ) -> list:
        arg_list: list = []

        for param in sig.parameters.values():
            # ic(param.name, param.empty, param.default, param.annotation, param.kind)

            if param.name == "self":
                pass
            else:
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    name = "*{}".format(param.name)
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    name = "**{}".format(param.name)
                elif param.default == inspect.Parameter.empty:
                    name = param.name
                else:
                    if isinstance(param.default, str):
                        default_repr = repr(param.default).replace("'", '"')
                    else:
                        default_repr = param.default

                    name = "{}={}".format(param.name, default_repr)

                anno = self.extract_type_annotation(param.annotation)
                arg_list.append((name, anno))

        return arg_list

    def extract_type_annotation(
        self,
        sig: inspect.Signature,
    ):
        type_name = str(sig)
        type_class = sig.__class__.__module__

        try:
            if type_class != "typing":
                if type_name.startswith("<class"):
                    type_name = type_name.split("'")[1]

            if type_name == "~AnyStr":
                type_name = "typing.AnyStr"
            elif type_name.startswith("~"):
                type_name = type_name[1:]

        except Exception:
            ic(type_name)
            traceback.print_exc()
        finally:
            return type_name

    def document_type(
        self,
        path_list: list,
        name: str,
        obj: typing.Any,
    ) -> typing.List[str]:
        local_md: typing.List[str] = []

        frag = ".".join(path_list + [name])
        anchor = "#### [`{}` {}](#{})".format(name, "type", frag)
        local_md.append(anchor)

        local_md.append("```python")
        local_md.append("{} = {}".format(name, obj))
        local_md.append("```")
        local_md.append("")

        return local_md

    def format_class(
        self,
        todo_list: typing.Dict[str, typing.Any],
        class_name: str,
    ) -> None:
        self.md.append("## [`{class_name}` class](#{class_name})".format(class_name=class_name))

        class_obj = todo_list[class_name]
        docstring = class_obj.__doc__

        if docstring:
            self.md.append(docstring)

        obj_md_pos: typing.Dict[int, typing.List[str]] = {}

        for member_name, member_obj in inspect.getmembers(class_obj):
            path_list = [self.module_name, class_name]

            if member_name.startswith("__") or not member_name.startswith("_"):
                if member_name not in class_obj.__dict__:
                    continue
                if inspect.isfunction(member_obj):
                    func_kind = "method"
                elif inspect.ismethod(member_obj):
                    func_kind = "classmethod"
                else:
                    continue

                line_num, obj_md = self.document_method(path_list, member_name, member_obj, func_kind)
                obj_md_pos[line_num] = obj_md

        for _pos, obj_md in sorted(obj_md_pos.items()):
            self.md.extend(obj_md)

    def format_functions(self) -> None:
        self.md.append("---")
        self.md.append("## [module functions](#{})".format(self.module_name))

        for func_name, func_obj in inspect.getmembers(self.module_obj, inspect.isfunction):
            if not func_name.startswith("_"):
                _line_num, obj_md = self.document_method([self.module_name], func_name, func_obj, "function")
                self.md.extend(obj_md)

    def format_types(self) -> None:
        self.md.append("---")
        self.md.append("## [module types](#{})".format(self.module_name))

        for name, obj in inspect.getmembers(self.module_obj):
            if obj.__class__.__module__ == "typing":
                if not str(obj).startswith("~"):
                    obj_md = self.document_type([self.module_name], name, obj)
                    self.md.extend(obj_md)


if __name__ == "__main__":
    pkg_doc = PackageDoc(
        "foo",
        "http://example.com/",
        [],
    )
