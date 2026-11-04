import logging

#                                                                     #
#                                                                     #
#                     PreTeXtFatal ("invalid source, or a severe bug") #
#                                                                     #
#                                                                     #

DEBUG_LEVEL = logging.DEBUG
INFO_LEVEL = logging.INFO
FALLBACK_LEVEL = 25
WARNING_LEVEL = logging.WARNING
ERROR_LEVEL = logging.ERROR
BUG_LEVEL = 45
FATAL_LEVEL = logging.CRITICAL
logging.addLevelName(FALLBACK_LEVEL, "FALLBACK")
logging.addLevelName(BUG_LEVEL, "BUG")
logging.addLevelName(FATAL_LEVEL, "FATAL")


class PreTeXtFatal(Exception):
    pass


log = logging.getLogger("ptxlogger")


def _log_fallback(message, *args, **kwargs):
    if log.isEnabledFor(FALLBACK_LEVEL):
        log._log(FALLBACK_LEVEL, message, args, **kwargs)


def _log_bug(message, *args, **kwargs):
    if log.isEnabledFor(BUG_LEVEL):
        log._log(BUG_LEVEL, message, args, **kwargs)


def _log_fatal(message, *args, **kwargs):
    log._log(FATAL_LEVEL, message, args, **kwargs)
    raise PreTeXtFatal(message)


log.fallback = _log_fallback
log.bug = _log_bug
log.fatal = _log_fatal


_XSL_MESSAGE_LEVELS = {
    "FATAL": FATAL_LEVEL,
    "BUG": BUG_LEVEL,
    "ERROR": ERROR_LEVEL,
    "FALLBACK": FALLBACK_LEVEL,
    "WARNING": WARNING_LEVEL,
    "DEPRECATE": WARNING_LEVEL,
    "INFO": INFO_LEVEL,
    "DEBUG": DEBUG_LEVEL,
}


def log_relayed_message(message, prefix=""):
    token = re.match(r"\s*PTX:([\w-]+)", message)
    display = prefix + message
    if token:
        level = _XSL_MESSAGE_LEVELS.get(token.group(1).upper())
        if level is not None:
            log.log(level, display)
        else:
            log.debug(display)
    elif re.match(r"\s*(?i:ptx|warning|error|fatal|bug|deprecate)\b", message):
        log.bug("a PreTeXt-style message has a malformed severity token: {}".format(display))
    else:
        log.info(display)


import re
import traceback
import os
import os.path
import shutil
import contextlib

__module_warning = "\n".join([
    'PTX ERROR: the "{}" module has failed to load, and',
    "  this is necessary for the task you have requested.  Perhaps",
    "  you have not installed it?  Or perhaps you have forgotten to",
    "  use a Python virtual environment you set up for this purpose?",
])

try:
    import lxml.etree as ET
except ImportError:
    raise ImportError(__module_warning.format("lxml"))


def get_web_asset(url):
    try:
        import requests
    except ImportError:
        msg = 'The "requests" module is not available and is necessary for downloading files.'
        log.debug(msg)
        raise Exception(msg)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    try:
        services_response = requests.get(url, timeout=(1, 10), headers=headers)
    except requests.exceptions.RequestException as e:
        msg = "\n".join([
            'There was a network problem while trying to download "{}"',
            "and the reported problem is:",
            "{}",
        ])
        log.debug(msg.format(url, e))
        raise Exception(msg.format(url, e))

    response_status_code = services_response.status_code
    if response_status_code != 200:
        msg = "\n".join(["The file {} was not found", "the server returned response code {}"])
        log.debug(msg.format(url, response_status_code))
        raise Exception(msg.format(url, response_status_code))

    return services_response.content


def download_file(url, dest_filename):
    contents = get_web_asset(url)
    try:
        dest_dir = os.path.dirname(dest_filename)
        os.makedirs(dest_dir, exist_ok=True)

        with open(dest_filename, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise Exception("Failed to save download", dest_filename)


def xsltproc(xsl, xml, result, output_dir=None, stringparams={}):
    import threading

    log.info("XSL conversion of {} by {}".format(xml, xsl))
    debug_string = "XSL conversion via {} of {} to {} and/or into directory {} with parameters {}"
    log.debug(debug_string.format(xsl, xml, result, output_dir, stringparams))

    stringparams = {key: ET.XSLT.strparam(value) for (key, value) in stringparams.items()}

    src_tree = guarded_xml_include_parser(xml)

    control = None
    if output_dir:
        control = ET.XSLTAccessControl(write_file=True)
    xsl_parser = ET.XMLParser(resolve_entities=True, no_network=True)
    xsl_tree = ET.parse(xsl, parser=xsl_parser)
    xslt = ET.XSLT(xsl_tree, access_control=control)

    owd = os.getcwd()
    if output_dir:
        os.chdir(output_dir)
    ET.clear_error_log()
    result_tree = []
    texc = None

    def transform():
        nonlocal result_tree, texc
        try:
            result_tree = xslt(src_tree, **stringparams)
        except Exception as e:
            texc = e

    try:
        parse_t = threading.Thread(target=transform)
        parse_t.start()
        still_alive = True
        start = 0
        while still_alive:
            parse_t.join(0.5)
            still_alive = parse_t.is_alive()

            end = len(xslt.error_log)

            if (start == 0) and (end > 0):
                log.info("messages from the log for XSL processing (prefaced with a *):")
            for line in xslt.error_log[start:end]:
                log_relayed_message(line.message, prefix="* ")
            start = end
        if texc is None:
            log.info("successful application of {}".format(xsl))
        else:
            raise (texc)
    except Exception as e:
        log.error("processing with {} has failed\n".format(xsl))
        raise (e)
    finally:
        if parse_t.is_alive():
            parse_t.join()
        os.chdir(owd)

    try:
        if result:
            result_tree.write_output(result)
        return result_tree
    except LookupError as e:
        root_cause = str(e)
        msg = "".join([
            "PTX:ERROR: the stylesheet: {}\n",
            "has a problem with xsl:output/@encoding.\n",
            "The lxml error message is:\n",
            '"{}"',
        ]).format(xsl, root_cause)
        raise ValueError(msg)


def guarded_xml_include_parser(xml):

    huge_parser = ET.XMLParser(huge_tree=True)
    src_tree = ET.parse(xml, parser=huge_parser)
    try:
        includer = ET.XInclude()
        includer(src_tree.getroot())
        if includer.error_log:
            namespace_xi_error = False
            log.debug("XInclude error(s) found:")
            for line in includer.error_log:
                log.debug(f"* {line.message}")
                if "Namespace prefix xi on include is not defined" in line.message:
                    log.error(
                        "You are trying to use 'xi:include' in a file that does not contain 'xmlns:xi=\"http://www.w3.org/2001/XInclude\"' in its root element."
                    )
                    namespace_xi_error = True
            if namespace_xi_error:
                raise ET.XIncludeError("Missing namespace declaration for 'xi'")
        return src_tree
    except ET.XIncludeError as e:
        import lxml.ElementInclude

        def my_loader(href, parse, encoding=None, parser=None):
            try:
                ret = lxml.ElementInclude._lxml_default_loader(href, parse, encoding, parser)
            except Exception as e:
                log.error(f"Error loading {href}: {e}")
                raise
            return ret

        src_tree = ET.parse(xml, parser=huge_parser)
        lxml.ElementInclude.include(src_tree, loader=my_loader, max_depth=100)
        return src_tree


def set_ptx_path(path=None):

    global __ptx_path

    if path:
        __ptx_path = path
    else:
        this_file_path = os.path.abspath(__file__)
        lib_path, _ = os.path.split(this_file_path)
        module_dir, _ = os.path.split(lib_path)
        __ptx_path, _ = os.path.split(module_dir)
    return None


def get_ptx_path():

    return __ptx_path


def get_ptx_xsl_path():

    return os.path.join(get_ptx_path(), "xsl")


def get_source_path(source_file):

    source_dir, _ = os.path.split(source_file)
    log.info("discovering source file's directory name: {}".format(source_dir))
    return os.path.normpath(source_dir)


def _git_symbolic_to_hash(symbolic):

    repo = get_ptx_path()
    commit_filename = os.path.join(repo, ".git", "refs", "heads", symbolic)
    try:
        with open(commit_filename, "r", encoding="utf-8") as f:
            return f.readline()[:-1]
    except Exception as e:
        log.debug("the full PreTeXt repository is not available, so the source commit cannot be determined")
        return None


def get_git_master_commit():
    return _git_symbolic_to_hash("master")


def get_git_head():

    import string

    repo = get_ptx_path()
    branch_filename = os.path.join(repo, ".git", "HEAD")
    try:
        with open(branch_filename, "r", encoding="utf-8") as f:
            head = f.readline()[:-1]
    except Exception as e:
        log.debug("the full PreTeXt repository is not available, so the source commit cannot be determined")
        return (None, None)

    if all(c in string.hexdigits for c in head):
        return (None, head)
    else:
        branch = head[16:]
        commit = _git_symbolic_to_hash(branch)
        return (branch, commit)


def build_info_message():
    branch, commit = get_git_head()
    master = get_git_master_commit()
    msg = 'built with {} using commit {} at tip of branch "{}" ("master": {})'
    return msg.format("pretext/pretext script", commit, branch, master)


def set_executables(adict):
    global __executables

    __executables = adict


def get_executable_cmd(exec_name):

    log.debug('locating "{}" in [executables] section of configuration file'.format(exec_name))
    if exec_name == "tex":
        msg = "\n".join([
            "'tex'  is deprecated as a key for a LaTeX executable (2022-01-31)'",
            "             and has been replaced by 'latex', 'pdflatex', or 'xelatex'.",
            "***  We will attempt to honor your existing LaTeX engine choice.                ***",
            '***  Edit the configuration file  ("pretext.cfg" or "project.ptx") accordingly  ***',
        ])
        log.warning(msg)
    config_cmd_line = __executables[exec_name].split()

    normalized_exec = shutil.which(config_cmd_line[0])

    error_messages = []
    if normalized_exec == None:
        error_messages += [
            "PTX:ERROR: cannot locate executable with configuration name `{}` as command `{}`".format(
                exec_name, config_cmd_line[0]
            ),
            '***  Edit the configuration file  ("pretext.cfg" or "project.ptx") and/or install  ***',
            "***  the necessary program and/or make sure the executable is on your PATH         ***",
        ]
    if error_messages:
        raise OSError("\n".join(error_messages))
    log.debug("{} executable: {}, options: {}".format(exec_name, config_cmd_line[0], " ".join(config_cmd_line[1:])))
    return config_cmd_line


def get_deprecated_tex_fallback(key):

    if not (key in __executables) and ("tex" in __executables):
        return "tex"
    else:
        return key


def sanitize_url(url):
    log.info("validating, cleaning server URL: {}".format(url))
    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))
    try:
        requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        root_cause = str(e)
        msg = "PTX:ERROR: there was a problem with the server URL, {}\n".format(url)
        raise ValueError(msg + root_cause)
    return url


def sanitize_alpha_num_underscore(param):
    import string

    allowed = set(string.ascii_letters + string.digits + "_")
    log.info("verifying parameter: {}".format(param))
    if not (set(param) <= allowed):
        raise ValueError("PTX:ERROR: param {} contains characters other than a-zA-Z0-9_ ".format(param))
    return param


def get_temporary_directory():
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="ptx-")
    __temps.append(temp_dir)
    return temp_dir


def get_output_filename(xml, out_file, dest_dir, suffix):

    if out_file:
        return out_file
    derivedname = os.path.splitext(os.path.split(xml)[1])[0] + suffix
    return os.path.join(dest_dir, derivedname)


def release_temporary_directories(any_log_level):

    global __temps

    if log.level > 10 or any_log_level:
        try:
            for td in __temps:
                log.info("Removing temporary directory {}".format(td))
                shutil.rmtree(td, ignore_errors=False)
                log.debug("Removed temporary directory {}".format(td))
        except Exception as e:
            log.warning(
                "Failed to remove temporary directories, starting with {} (and maybe some others): {}".format(
                    td, str(e)
                )
            )
        finally:
            __temps = []
    else:
        log.debug("Temporary directories left behind for inspection: {}".format(__temps))


def verify_input_directory(inputdir):

    log.info("verifying and expanding input directory: {}".format(inputdir))
    if not (os.path.isdir(inputdir)):
        raise ValueError("directory {} does not exist".format(inputdir))
    absdir = os.path.abspath(inputdir)
    log.info("input directory expanded to absolute path: {}".format(absdir))
    return absdir


def get_managed_directories(xml_source, pub_file):

    gen_attr = "generated"
    ext_attr = "external"

    source_dir = get_source_path(xml_source)
    src_abs_path_error = " ".join([
        "the directory path for a managed directory, given in the",
        'source file as "directories/@{}" within "docinfo" must be relative to',
        'the PreTeXt source file location, and not the absolute path "{}"',
    ])
    src_missing_dir_error = " ".join([
        'the directory "{}" implied by the value "{}" in the',
        '"directories/@{}" entry within "docinfo" of the source file does not',
        "exist. Check the spelling, create the necessary directory, or remove",
        "the attribute.",
    ])
    pub_abs_path_error = " ".join([
        "the directory path for a managed directory, given in the",
        'publisher file as "source/directories/@{}" must be relative to',
        'the PreTeXt source file location, and not the absolute path "{}"',
    ])
    pub_missing_dir_error = " ".join([
        'the directory "{}" implied by the value "{}" in the',
        '"source/directories/@{}" entry of the publisher file does not',
        "exist. Check the spelling, create the necessary directory, or entirely",
        'remove the whole "source/directories" element of the publisher file.',
    ])
    gen_missing_dir_note = " ".join([
        'the generated directory "{}" does not exist yet.  Its contents',
        "are machine-made, so this is routine: it will appear when assets",
        "are first generated, and until then there is nothing to collect.",
    ])

    generated = None
    external = None

    src_tree = guarded_xml_include_parser(xml_source)
    directories_list = src_tree.xpath("/pretext/docinfo/directories")
    if directories_list:
        attributes_dict = directories_list[0].attrib
        if ext_attr in attributes_dict.keys():
            raw_path = attributes_dict[ext_attr]
            if os.path.isabs(raw_path):
                raise ValueError(src_abs_path_error.format(ext_attr, raw_path))
            else:
                abs_path = os.path.join(source_dir, raw_path)
            try:
                external = verify_input_directory(abs_path)
            except:
                raise ValueError(src_missing_dir_error.format(abs_path, raw_path, ext_attr))

    if pub_file:
        pub_tree = ET.parse(pub_file)
        pub_tree.xinclude()
        element_list = pub_tree.xpath("/publication/source/directories")
        if element_list:
            attributes_dict = element_list[0].attrib
            if gen_attr in attributes_dict.keys():
                raw_path = attributes_dict[gen_attr]
                if os.path.isabs(raw_path):
                    raise ValueError(pub_abs_path_error.format(gen_attr, raw_path))
                else:
                    abs_path = os.path.join(source_dir, raw_path)
                generated = os.path.abspath(abs_path)
                if not os.path.isdir(generated):
                    log.debug(gen_missing_dir_note.format(generated))
            if ext_attr in attributes_dict.keys():
                if external is not None:
                    log.warning(
                        " ".join([
                            "the external directory is specified both within",
                            '"docinfo" ("directories/@external") and in the publisher',
                            'file ("source/directories/@external").  The "docinfo"',
                            "value is used; please remove the publisher file entry.",
                        ])
                    )
                else:
                    log.warning(
                        " ".join([
                            "(2026-07-30) the external directory is a property of your",
                            "source, and is now declared with a",
                            '"directories/@external" attribute within "docinfo".',
                            'The publisher file entry "source/directories/@external"',
                            "is honored meanwhile, but please relocate it.",
                        ])
                    )
                    raw_path = attributes_dict[ext_attr]
                    if os.path.isabs(raw_path):
                        raise ValueError(pub_abs_path_error.format(ext_attr, raw_path))
                    else:
                        abs_path = os.path.join(source_dir, raw_path)
                    try:
                        external = verify_input_directory(abs_path)
                    except:
                        raise ValueError(pub_missing_dir_error.format(abs_path, raw_path, ext_attr))

    if generated is None:
        generated = os.path.abspath(os.path.join(source_dir, "generated"))
        if not os.path.isdir(generated):
            log.debug(gen_missing_dir_note.format(generated))

    return (generated, external)


def get_source_directories(xml_source):

    data_attr = "data"

    source_dir = get_source_path(xml_source)

    source_abs_path_error = " ".join([
        "the directory path for a managed directory, given in the",
        'source file as "docinfo/directories/@{}" must be relative to',
        'the PreTeXt source file location, and not the absolute path "{}"',
    ])
    source_missing_dir_error = " ".join([
        'the directory "{}" implied by the value "{}" in the',
        '"docinfo/directories/@{}" entry of the source file does not',
        "exist. Check the spelling, create the necessary directory, or entirely",
        'remove the whole "docinfo/directories" element of the source file.',
    ])

    data = None

    src_tree = guarded_xml_include_parser(xml_source)
    directories_list = src_tree.xpath("/pretext/docinfo/directories")
    if directories_list:
        attributes_dict = directories_list[0].attrib
        if data_attr in attributes_dict:
            raw_path = attributes_dict[data_attr]
            if os.path.isabs(raw_path):
                raise ValueError(source_abs_path_error.format(data_attr, raw_path))
            else:
                abs_path = os.path.join(source_dir, raw_path)
            try:
                data = verify_input_directory(abs_path)
            except:
                raise ValueError(source_missing_dir_error.format(abs_path, raw_path, data_attr))

    return data


def get_platform_host(pub_file):

    if not (pub_file):
        return "web"

    pub_tree = ET.parse(pub_file)
    pub_tree.xinclude()
    element_list = pub_tree.xpath("/publication/html/platform")
    if not (element_list):
        return "web"

    platform = element_list[0]
    attrs = platform.attrib
    if not ("host") in attrs:
        return "web"

    return attrs["host"]


def copy_managed_directories(build_dir, external_abs=None, generated_abs=None, data_abs=None):
    if external_abs is not None and os.path.isdir(external_abs):
        external_dir = os.path.join(build_dir, "external")
        shutil.copytree(external_abs, external_dir)

    if generated_abs is not None and os.path.isdir(generated_abs):
        generated_dir = os.path.join(build_dir, "generated")
        shutil.copytree(generated_abs, generated_dir)

    if data_abs is not None and os.path.isdir(data_abs):
        data_dir = os.path.join(build_dir, "data")
        shutil.copytree(data_abs, data_dir)


def copy_managed_resources(
    build_dir,
    external_abs=None,
    external_resources=None,
    generated_abs=None,
    generated_resources=None,
    data_abs=None,
    data_resources=None,
):
    def _copy_resources(root_abs, resources, dest_name):
        if not resources:
            if root_abs is None:
                return
        elif root_abs is None:
            raise ValueError("{}_resources was given without {}_abs to resolve it against".format(dest_name, dest_name))
        folders = {os.path.dirname(resource) for resource in resources}
        dest_root = os.path.join(build_dir, dest_name)
        for folder in folders:
            src = os.path.join(root_abs, folder)
            dst = os.path.join(dest_root, folder)
            shutil.copytree(src, dst, dirs_exist_ok=True)

    _copy_resources(external_abs, external_resources, "external")
    _copy_resources(generated_abs, generated_resources, "generated")
    _copy_resources(data_abs, data_resources, "data")


def copy_build_directory(build_dir, dest_dir):

    for filename in os.listdir(build_dir):
        src = os.path.join(build_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dest_dir)
        elif os.path.isdir(src):
            dest = os.path.join(dest_dir, filename)
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            msg = "the build directory {} contained an unexpected object, {}"
            log.debug(msg.format(build_dir, src))


def targz(output, source_dir):
    import tarfile

    with tarfile.open(output, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


@contextlib.contextmanager
def working_directory(path):
    current_directory = os.getcwd()
    os.chdir(path)
    log.debug(f"Now working in directory {path}")
    try:
        yield
    finally:
        os.chdir(current_directory)
        log.debug(f"Successfully changed directory back to {current_directory}")


def get_publisher_variable_report(xml_source, pub_file, params):

    log.debug("parsing the publisher file variables")

    params = params.copy()

    if pub_file:
        params["publisher"] = pub_file

    reporting_xslt = os.path.join(get_ptx_xsl_path(), "utilities", "report-publisher-variables.xsl")
    params["assembly.version-only"] = "yes"

    tmp_dir = get_temporary_directory()
    log.debug("temporary directory for publisher variables: {}".format(tmp_dir))
    temp_file = os.path.join(tmp_dir, "pub_var.txt")
    log.debug("file of publisher variables: {}".format(temp_file))

    xsltproc(reporting_xslt, xml_source, temp_file, None, params)

    variables = {}
    with open(temp_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 1:
                variables[parts[0]] = ""
            else:
                variables[parts[0]] = " ".join(parts[1:])

    return variables


def get_publisher_variable(variable_dict, variable_name):

    log.debug("determining value of publisher variable '{}'".format(variable_name))

    if variable_name in variable_dict:
        return variable_dict[variable_name]
    else:
        msg = "\n".join([
            "the publisher variable '{}' could not be located.",
            "Did you spell it correctly or does it need implementation?",
            "If the latter, read instructions in code comments in the relevant routines.",
        ])
        raise ValueError(msg.format(variable_name))


__ptx_path = None
set_ptx_path()

__executables = None

__temps = []
