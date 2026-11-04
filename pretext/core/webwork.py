import logging

log = logging.getLogger("ptxlogger")

import os
import os.path
import re
import shutil
import subprocess

from . import common

__module_warning = common.__module_warning
import lxml.etree as ET


def webwork_to_xml(xml_source, pub_file, stringparams, xmlid_root, abort_early, server_params, dest_dir):
    import urllib.parse
    import copy
    import tarfile

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))

    generated_dir, external_dir = common.get_managed_directories(xml_source, pub_file)
    if not generated_dir:
        msg = "".join([
            "a publisher file specifying /publication/source/directories/@generated ",
            "is not in use. WeBWorK representations will be in {}",
        ])
        log.warning(msg.format(dest_dir))
    ww_reps_dir = dest_dir
    ww_images_dir = os.path.join(dest_dir, "images")

    ww_pg_dir = os.path.join(ww_reps_dir, "pg")

    if not (os.path.isdir(ww_reps_dir)):
        os.mkdir(ww_reps_dir)
    if not (os.path.isdir(ww_images_dir)):
        os.mkdir(ww_images_dir)
    if not (os.path.isdir(ww_pg_dir)):
        os.mkdir(ww_pg_dir)

    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-pg.xsl")

    tmp_dir = common.get_temporary_directory()
    extracted_pg_filename = os.path.join(tmp_dir, "extracted-pg.xml")
    log.debug("Exctracted PG temporarily in {}".format(extracted_pg_filename))
    common.xsltproc(extraction_xslt, xml_source, extracted_pg_filename, None, stringparams)

    extracted_pg_xml = ET.parse(extracted_pg_filename).getroot()
    localization = extracted_pg_xml.get("localization")
    webwork2_server = extracted_pg_xml.find("server-params-pub").get("webwork2-server")
    numbered_title_filesafe = extracted_pg_xml.get("numbered-title-filesafe")
    ww_project_dir = os.path.join(ww_reps_dir, "pg", numbered_title_filesafe)
    if not (os.path.isdir(ww_project_dir)):
        os.mkdir(ww_project_dir)
    ww_macros_dir = os.path.join(ww_project_dir, "macros")
    if not (os.path.isdir(ww_macros_dir)):
        os.mkdir(ww_macros_dir)

    webwork_sets(xml_source, pub_file, stringparams, ww_pg_dir, False, False)
    pg_macros(xml_source, pub_file, stringparams, ww_macros_dir)

    no_publication_file = False
    if webwork2_server is not None:
        server_params_pub = {
            "webwork2_domain": webwork2_server,
            "courseID": extracted_pg_xml.find("server-params-pub").get("course-id"),
            "user": extracted_pg_xml.find("server-params-pub").get("user-id"),
            "passwd": extracted_pg_xml.find("server-params-pub").get("password"),
            "disableCookies": "1",
        }
        static_processing = extracted_pg_xml.find("processing").attrib["static"]
        pg_location = extracted_pg_xml.find("processing").attrib["pg-location"]
    else:
        no_publication_file = True
        server_params_pub = {
            "webwork2_domain": "https://webwork-ptx.aimath.org",
            "courseID": "anonymous",
            "user": "anonymous",
            "passwd": "anonymous",
            "disableCookies": "1",
        }
        static_processing = "webwork2"
        pg_location = "/opt/webwork/pg"

    if no_publication_file and server_params is None:
        raise ValueError("Either use a publication file or pass a --server argument")
    elif no_publication_file:
        log.warning(
            "WeBWorK server declared using -s argument.\n"
            + "              Please consider using a publication file with publication/webwork instead."
        )
        server_params = server_params.strip()
        if server_params.startswith("(") and server_params.endswith(")"):
            server_params = server_params.strip("()")
            split_server_params = server_params.split(",")
            webwork2_domain = common.sanitize_url(split_server_params[0])
            courseID = common.sanitize_alpha_num_underscore(split_server_params[1])
            user = common.sanitize_alpha_num_underscore(split_server_params[2])
            passwd = common.sanitize_alpha_num_underscore(split_server_params[3])
        else:
            webwork2_domain = common.sanitize_url(server_params)
            courseID = "anonymous"
            user = "anonymous"
            passwd = "anonymous"
    else:
        if server_params is not None:
            log.warning(
                "Publication file in use and -s argument passed for WeBWorK server.\n"
                + "              -s argument will be ignored.\n"
                + "              Using publication/webwork values (or defaults) instead."
            )
        webwork2_domain = common.sanitize_url(server_params_pub["webwork2_domain"])
        courseID = server_params_pub["courseID"]
        user = server_params_pub["user"]
        passwd = server_params_pub["passwd"]

    webwork2_domain_webwork2 = webwork2_domain + "/webwork2/"
    webwork2_render_rpc = webwork2_domain_webwork2 + "render_rpc"

    webwork2_version = None
    webwork2_major_version = None
    webwork2_minor_version = None

    need_for_webwork2 = (static_processing == "webwork2") or (extracted_pg_xml.xpath("//problem[@origin='webwork2']"))

    need_for_socket = (static_processing == "local") and (extracted_pg_xml.xpath("//problem[@origin!='webwork2']"))

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    try:
        params_for_version_determination = dict(
            problemSeed=1,
            displayMode="PTX",
            courseID=courseID,
            user=user,
            userID=user,
            passwd=passwd,
            disableCookies="1",
            outputformat="raw",
        )
        render_rpc_response = requests.get(url=webwork2_render_rpc, params=params_for_version_determination)
        if render_rpc_response.status_code == 200:
            version_determination_json = render_rpc_response.json()
            if "ww_version" in version_determination_json:
                webwork2_version = version_determination_json["ww_version"]
                webwork2_version_match = re.search(r"((\d+)\.(\d+)(\+develop)?)", webwork2_version, re.I)
    except Exception as e:
        root_cause = str(e)
        msg = "PTX:ERROR:   There was a problem contacting the WeBWorK server.\n"
        raise ValueError(msg.format(webwork2_domain_webwork2) + root_cause)

    if webwork2_version == None:
        try:
            landing_page = requests.get(webwork2_domain_webwork2)
        except Exception as e:
            root_cause = str(e)
            msg = (
                "PTX:ERROR:   There was a problem contacting the WeBWorK server.\n"
                + "             Is there a WeBWorK landing page at {}?\n"
            )
            raise ValueError(msg.format(webwork2_domain_webwork2) + root_cause)
        landing_page_text = landing_page.text

        webwork2_version_match = re.search(r"WW.VERSION:\s*((\d+)\.(\d+)(\+develop)?)", landing_page_text, re.I)

    try:
        webwork2_version = webwork2_version_match.group(1)
        webwork2_major_version = int(webwork2_version_match.group(2))
        webwork2_minor_version = int(webwork2_version_match.group(3))
    except AttributeError as e:
        root_cause = str(e)
        msg = (
            "PTX:ERROR:   PreTeXt was unable to discern the version of the WeBWorK server.\n"
            + "                         Is there a WeBWorK landing page at {}?\n"
            + "                         And does it display the WeBWorK version?\n"
        )
        raise ValueError(msg.format(webwork2_version, webwork2_domain))

    webwork2_path = webwork2_render_rpc

    origin = {}
    copied_from = {}
    seed = {}
    path = {}
    pghuman = {}
    pgdense = {}
    for problem in extracted_pg_xml.iter("problem"):
        origin[problem.get("id")] = problem.get("origin")
        seed[problem.get("id")] = problem.get("seed")
        path[problem.get("id")] = problem.get("path")
        if problem.get("copied-from") is not None:
            copied_from[problem.get("id")] = problem.get("copied-from")
        else:
            copied_from[problem.get("id")] = None
        if problem.get("origin") == "generated":
            pghuman[problem.get("id")] = problem.find("pghuman").text
            pgdense[problem.get("id")] = problem.find("pgdense").text

    if webwork2_major_version != 2 or webwork2_minor_version < 19:
        msg = (
            "PTX:ERROR:   PreTeXt supports WeBWorK 2.19 and later, and it appears you are attempting to use version: {}\n"
            + "                         Server: {}\n"
            + "                         You may want to use the AIM WeBWorK server at webwork-ptx.aimath.org.\n"
        )
        raise ValueError(msg.format(webwork2_version, webwork2_domain))

    if need_for_webwork2:
        webwork2_session = requests.Session()

    clientsocket = None

    if need_for_socket:
        import socket
        import json

        perl_executable_cmd = common.get_executable_cmd("perl")[0]
        pgscript = os.path.join(common.get_ptx_path(), "script", "webwork", "pg-ptx.pl")

        extra_macro_dirs = []

        if os.path.exists(ww_macros_dir):
            extra_macro_dirs.append("--extraMacroDir")
            extra_macro_dirs.append(ww_macros_dir)

        if os.path.exists(os.path.join(external_dir, "macros")):
            extra_macro_dirs.append("--extraMacroDir")
            extra_macro_dirs.append(os.path.join(external_dir, "macros"))

        proc = subprocess.Popen(
            [
                perl_executable_cmd,
                pgscript,
                "--externalFileDir",
                external_dir,
                "--tempDirectory",
                tmp_dir,
                *extra_macro_dirs,
            ],
            stdin=None,
            stdout=None,
            stderr=None,
            env={"PG_ROOT": pg_location, "MOJO_MODE": "production"},
        )
        clientsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        count = 1
        while count > 0 and count < 10:
            try:
                clientsocket.connect(tmp_dir + "/pg-ptx.sock")
                count = 0
            except:
                ++count
        if count > 0:
            raise ValueError("PTX:ERROR: unable to establish connection to local socket")

    NSMAP = {"xml": "http://www.w3.org/XML/1998/namespace"}
    XML = "http://www.w3.org/XML/1998/namespace"
    for problem in origin:
        if origin[problem] == "webwork2":
            msg = "building representations of webwork2-hosted WeBWorK problem"
        elif origin[problem] == "generated":
            msg = "building representations of generated WeBWorK problem"
        else:
            raise ValueError(
                "PTX:ERROR: problem origin should be 'webwork2' or 'generated', not '{}'".format(origin[problem])
            )
        log.info(msg)

        if static_processing == "local" and origin[problem] != "webwork2":
            socket_params = {"problemSeed": seed[problem], "problemUUID": problem}

            if origin[problem] == "generated":
                socket_params["source"] = pgdense[problem]
            else:
                socket_params["sourceFilePath"] = os.path.join(external_dir, path[problem])

            msg = "sending {} to socket to save in {}: origin is '{}'"
            log.info(msg.format(problem, ww_reps_dir, origin[problem]))
            clientsocket.send(json.dumps(socket_params).encode("utf-8"))

            buffer = bytearray()
            while True:
                received = clientsocket.recv(4096)
                if not received:
                    break
                buffer.extend(received)
                if buffer.endswith(b"ENDOFSOCKETDATA"):
                    break

            response = buffer.decode().replace("ENDOFSOCKETDATA", "")

        else:
            if origin[problem] == "webwork2":
                server_params_source = {"sourceFilePath": path[problem]}
            else:
                server_params_source = {"rawProblemSource": pgdense[problem]}

            server_params = {
                "showSolutions": "1",
                "showHints": "1",
                "displayMode": "PTX",
                "courseID": courseID,
                "user": user,
                "passwd": passwd,
                "outputformat": "ptx",
                "disableCookies": "1",
                "problemSeed": seed[problem],
                "problemUUID": problem,
            }
            server_params.update(server_params_source)

            msg = "sending {} to server to save in {}: origin is '{}'"
            log.info(msg.format(problem, ww_reps_dir, origin[problem]))
            if origin[problem] == "webwork2":
                log.debug("server-to-ptx: {}\n{}\n{}\n{}".format(problem, webwork2_path, path[problem], ww_reps_dir))
            elif origin[problem] == "generated":
                log.debug("server-to-ptx: {}\n{}\n{}\n{}".format(problem, webwork2_path, pgdense[problem], ww_reps_dir))

            try:
                response = webwork2_session.post(webwork2_path, data=server_params)
                log.debug("Getting problem response from: " + response.url)

            except requests.exceptions.RequestException as e:
                root_cause = str(e)
                msg = "PTX:ERROR: there was a problem collecting a problem,\n Server: {}\nRequest Parameters: {}\n"
                raise ValueError(msg.format(webwork2_path, server_params) + root_cause)

            response = response.text

        no_compile = "ERROR caught by Translator while processing" in response

        bad_xml = False
        try:
            response_root = ET.fromstring(bytes(response, encoding="utf-8"))
        except:
            response_root = ET.Element("webwork")
            bad_xml = True

        no_statement = False
        if not bad_xml:
            if response_root.find(".//statement") is None:
                no_statement = True
        badness = no_compile or bad_xml or no_statement

        badness_msg = ""
        badness_tip = ""
        badness_type = ""
        badness_base64 = ""
        if no_compile:
            badness_msg = "PTX:ERROR: WeBWorK problem {} with seed {} is either empty or failed to compile  \n{}\n"
            badness_tip = (
                "  Use -a to halt with full PG and returned content"
                if (origin[problem] == "generated")
                else "  Use -a to halt with returned content"
            )
            badness_type = "compile"
            badness_base64 = "RE9DVU1FTlQoKTsKbG9hZE1hY3JvcygnUEdzdGFuZGFyZC5wbCcpOwpURVhUKCdXZUJXb3JLIFByb2JsZW0gRG9lcyBOb3QgRXhpc3QgT3IgRGlkIE5vdCBDb21waWxlJyk7CkVORERPQ1VNRU5UKCk7"
        elif bad_xml:
            badness_msg = "PTX:ERROR: WeBWorK problem {} with seed {} does not return valid XML  \n  It may not be PTX compatible  \n{}\n"
            badness_tip = "  Use -a to halt with returned content"
            badness_type = "xml"
            badness_base64 = "RE9DVU1FTlQoKTsKbG9hZE1hY3JvcygnUEdzdGFuZGFyZC5wbCcpOwpURVhUKCdXZUJXb3JLIFByb2JsZW0gRGlkIE5vdCBHZW5lcmF0ZSBWYWxpZCBYTUwnKTsKRU5ERE9DVU1FTlQoKTs="
        elif no_statement:
            badness_msg = "PTX:ERROR: WeBWorK problem {} with seed {} does not have a statement tag \n  Maybe it uses something other than BEGIN_TEXT or BEGIN_PGML to print the statement in its PG code \n{}\n"
            badness_tip = "  Use -a to halt with returned content"
            badness_type = "statement"
            badness_base64 = "RE9DVU1FTlQoKTsKbG9hZE1hY3JvcygnUEdzdGFuZGFyZC5wbCcpOwpURVhUKCdXZUJXb3JLIFByb2JsZW0gRGlkIE5vdCBIYXZlIGEgInN0YXRlbWVudCIgVGFnJyk7CkVORERPQ1VNRU5UKCk7"

        if abort_early:
            if badness:
                debugging_help = response
                if origin[problem] == "generated" and no_compile:
                    debugging_help += "\n" + pghuman[problem]
                raise ValueError(badness_msg.format(path[problem], seed[problem], debugging_help))

        verbatim_split = re.split(r"(\\verb\x1F.*?\x1F|\\verb\r.*?\r)", response)
        response_text = ""
        for item in verbatim_split:
            if re.match(r"^\\verb(\x1F|\r).*?\1$", item):
                (original_delimiter, verbatim_content) = re.search(r"\\verb(\x1F|\r)(.*?)\1", item).group(1, 2)
                if set(["#", "%", "&", "<", ">", "\\", "^", "_", "`", "|", "~"]).intersection(
                    set(list(verbatim_content))
                ):
                    index = 33
                    while index < 127:
                        if index in [42, 34, 38, 39, 59, 60, 62] or chr(index) in verbatim_content:
                            index += 1
                        else:
                            break
                    if index == 127:
                        log.warning("Could not find delimiter for verbatim expression")
                        return "!Could not find delimiter for verbatim expression.!"
                    else:
                        response_text += item.replace(original_delimiter, chr(index))
                else:
                    text_content = verbatim_content.replace("$", "\\$")
                    text_content = text_content.replace("{", "\\{")
                    text_content = text_content.replace("}", "\\}")
                    response_text += "\\text{" + text_content + "}"
            else:
                response_text += item

        graphics_pattern = re.compile(r'<image.*?source="([^"]+)"')

        count = 0
        for match in re.finditer(graphics_pattern, response_text):
            ww_image_full_path = match.group(1)
            if static_processing == "local" and origin[problem] != "webwork2":
                ww_image_scheme = ""
            else:
                ww_image_url = urllib.parse.urljoin(webwork2_domain, ww_image_full_path)
                ww_image_url_parsed = urllib.parse.urlparse(ww_image_url)
                ww_image_scheme = ww_image_url_parsed.scheme
                ww_image_full_path = ww_image_url_parsed.path
            count += 1
            ww_image_path, ww_image_filename = os.path.split(ww_image_full_path)
            ww_image_name, image_extension = os.path.splitext(ww_image_filename)
            ptx_image_name = problem + "-image-" + str(count)
            ptx_image_filename = ptx_image_name + image_extension
            if image_extension == ".tgz":
                ptx_image = ptx_image_name
            else:
                ptx_image = ptx_image_name + image_extension
            if ww_image_scheme:
                image_url = ww_image_url
            else:
                image_url = urllib.parse.urljoin(webwork2_domain, ww_image_full_path)
            if generated_dir:
                if "xmlns:pi=" not in response_text:
                    response_text = response_text.replace(
                        "<webwork>",
                        '<webwork xmlns:pi="http://pretextbook.org/2020/pretext/internal">',
                    )
                response_text = re.sub(
                    r"(<image[^>]*? )source=",
                    r"\1pi:generated=",
                    response_text,
                    count=0,
                    flags=0,
                )
                response_text = response_text.replace(ww_image_full_path, "webwork/images/" + ptx_image)
            else:
                response_text = response_text.replace(ww_image_full_path, "images/" + ptx_image)
            if static_processing == "local" and origin[problem] != "webwork2":
                image_local_path = ww_image_full_path.replace("/pg_files/tmp", tmp_dir)
                destination_image_file = os.path.join(ww_images_dir, ptx_image_filename)

                try:
                    log.info(
                        "saving image file {} {} in {}".format(
                            ptx_image_filename, "(contents)" if image_extension == ".tgz" else "", ww_images_dir
                        )
                    )
                    shutil.copy2(image_local_path, destination_image_file)
                except Exception as e:
                    raise ValueError(
                        "PTX:ERROR:   There was an error copying the image file {} to {}.\n".format(
                            image_local_path, destination_image_file
                        )
                        + str(e)
                    )
            else:
                try:
                    image_response = webwork2_session.get(image_url)
                except requests.exceptions.RequestException as e:
                    root_cause = str(e)
                    msg = "PTX:ERROR: there was a problem downloading an image file,\n URL: {}\n"
                    raise ValueError(msg.format(image_url) + root_cause)
                destination_image_file = os.path.join(ww_images_dir, ptx_image_filename)
                try:
                    with open(destination_image_file, "wb") as image_file:
                        msg = "saving image file {} {} in {}"
                        qualifier = ""
                        if image_extension == ".tgz":
                            qualifier = "(contents)"
                        log.info(msg.format(ptx_image_filename, qualifier, ww_images_dir))
                        image_file.write(image_response.content)
                except Exception as e:
                    root_cause = str(e)
                    msg = "PTX:ERROR: there was a problem saving an image file,\n Filename: {}\n"
                    raise ValueError(msg.format(destination_image_file) + root_cause)
            if image_extension == ".tgz":
                tgzfile = tarfile.open(destination_image_file)
                tgzfile.extractall(os.path.join(ww_images_dir))
                tgzfile.close()
                for ext in ["tex", "pdf", "svg", "png"]:
                    try:
                        os.replace(
                            os.path.join(ww_images_dir, "image.{}".format(ext)),
                            os.path.join(ww_images_dir, ptx_image_name + ".{}".format(ext)),
                        )
                    except:
                        msg = "{} did not contain a .{} file"
                        log.warning(msg.format(destination_image_file, ext))
                os.remove(os.path.join(ww_images_dir, ptx_image_filename))

        webwork_reps = ET.Element("webwork-reps", nsmap=NSMAP)
        webwork_reps.set("version", "2")
        webwork_reps.set("webwork2_major_version", str(webwork2_major_version))
        webwork_reps.set("webwork2_minor_version", str(webwork2_minor_version))
        webwork_reps.set("{%s}id" % (XML), "extracted-" + problem)
        webwork_reps.set("assembly-id", problem)
        static = ET.SubElement(webwork_reps, "static")
        static.set("seed", seed[problem])
        if origin[problem] == "webwork2":
            static.set("source", path[problem])

        if badness:
            log.error(badness_msg.format(path[problem], seed[problem], badness_tip))
            static.set("failure", badness_type)
            statement = ET.SubElement(static, "statement")
            p = ET.SubElement(statement, "p")
            p.text = badness_msg.format(path[problem], seed[problem], badness_tip)
        else:
            response_root = ET.fromstring(bytes(response_text, encoding="utf-8"))

            def static_webwork_level(write, read):

                tasks = read.findall("./task")
                if tasks:
                    titles = read.xpath("./title")
                    if titles:
                        for ttl in list(titles):
                            title = copy.deepcopy(ttl)
                            write.append(title)
                    introductions = read.xpath(
                        "./statement[following-sibling::task]|./statement[following-sibling::stage]"
                    )
                    if introductions:
                        introduction = ET.SubElement(write, "introduction")
                        for intro in list(introductions):
                            for child in intro:
                                chcopy = copy.deepcopy(child)
                                introduction.append(chcopy)
                    for tsk in list(tasks):
                        task = ET.SubElement(write, "task")
                        static_webwork_level(task, tsk)
                    conclusions = read.xpath("./statement[preceding-sibling::task]")
                    if conclusions:
                        conclusion = ET.SubElement(write, "conclusion")
                        for conc in list(conclusions):
                            for child in conc:
                                chcopy = copy.deepcopy(child)
                                conclusion.append(chcopy)
                else:
                    titles = read.xpath("./title")
                    if titles:
                        for ttl in list(titles):
                            title = copy.deepcopy(ttl)
                            write.append(title)
                    statements = read.xpath("./statement[not(preceding-sibling::task or following-sibling::task)]")
                    if statements:
                        statement = ET.SubElement(write, "statement")
                        for stat in list(statements):
                            for child in stat:
                                chcopy = copy.deepcopy(child)
                                statement.append(chcopy)
                    hints = read.xpath("./hint")
                    if hints:
                        hint = ET.SubElement(write, "hint")
                        for hnt in list(hints):
                            for child in hnt:
                                chcopy = copy.deepcopy(child)
                                hint.append(chcopy)
                    answer_names = read.xpath(".//fillin/@name|.//var/@name|.//ul/@name|.//ol/@name|.//dl/@name")
                    answer_hashes = response_root.find("./answerhashes")
                    if answer_hashes is not None:
                        for ans in list(answer_hashes):
                            if ans.get("ans_name") in list(answer_names):
                                correct_ans = ans.get("correct_ans", "")
                                correct_ans_latex_string = ans.get("correct_ans_latex_string", "")
                                if correct_ans != "" or correct_ans_latex_string != "":
                                    answer = ET.SubElement(write, "answer")
                                    p = ET.SubElement(answer, "p")
                                    if correct_ans_latex_string:
                                        m = ET.SubElement(p, "m")
                                        m.text = correct_ans_latex_string
                                    elif correct_ans:
                                        p.text = correct_ans
                    solutions = read.xpath("./solution")
                    if solutions:
                        solution = ET.SubElement(write, "solution")
                        for sol in list(solutions):
                            for child in sol:
                                chcopy = copy.deepcopy(child)
                                solution.append(chcopy)

            static_webwork_level(static, response_root)

        if badness or origin[problem] == "generated":
            source_key = "problemSource"
        else:
            source_key = "sourceFilePath"

        if badness:
            source_value = badness_base64
        else:
            if origin[problem] == "webwork2":
                source_value = path[problem]
            else:
                if copied_from[problem] is not None:
                    source_value = path[copied_from[problem]]
                else:
                    source_value = path[problem]

        rendering_data = ET.SubElement(webwork_reps, "rendering-data")
        rendering_data.set(source_key, source_value)
        rendering_data.set("origin", origin[problem])
        rendering_data.set("domain", webwork2_domain)
        rendering_data.set("course-id", courseID)
        rendering_data.set("user-id", user)
        rendering_data.set("passwd", passwd)
        rendering_data.set("language", localization)

        pg = ET.SubElement(webwork_reps, "pg")
        try:
            pg.set("copied-from", copied_from[problem])
        except Exception:
            pass

        if origin[problem] == "generated":
            if badness:
                pg_shell = "DOCUMENT();\nloadMacros('PGstandard.pl','PGML.pl','PGcourse.pl');\nBEGIN_PGML\n{}END_PGML\nENDDOCUMENT();"
                formatted_pg = pg_shell.format(badness_msg.format(path[problem], seed[problem], badness_tip))
            else:
                formatted_pg = pghuman[problem]
            pg.text = ET.CDATA("\n" + formatted_pg)
        elif origin[problem] == "webwork2":
            pg.set("source", path[problem])

        include_file_name = os.path.join(ww_reps_dir, problem + ".xml")
        try:
            with open(include_file_name, "wb") as include_file:
                include_file.write(
                    ET.tostring(
                        webwork_reps,
                        encoding="utf-8",
                        xml_declaration=True,
                        pretty_print=True,
                    )
                )
        except Exception as e:
            root_cause = str(e)
            msg = "PTX:ERROR: there was a problem writing a problem to the file: {}\n"
            raise ValueError(msg.format(include_file_name) + root_cause)

    try:
        webwork2_session.close()
    except:
        pass

    if clientsocket:
        clientsocket.send(b"quit")


def webwork_sets(xml_source, pub_file, stringparams, dest_dir, tgz, need_macros):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "pretext-ww-problem-sets.xsl")
    tmp_dir = common.get_temporary_directory()
    common.xsltproc(extraction_xslt, xml_source, None, output_dir=tmp_dir, stringparams=stringparams)
    set_folders = os.listdir(tmp_dir)
    if not set_folders:
        log.info("no WeBWorK problem sets to construct")
        return
    folder_name = set_folders[0]
    folder = os.path.join(tmp_dir, folder_name)
    macros_folder = os.path.join(folder, "macros")
    os.mkdir(macros_folder)
    if need_macros:
        pg_macros(xml_source, pub_file, stringparams, macros_folder)
    if tgz:
        archive_file = os.path.join(tmp_dir, folder_name + ".tgz")
        common.targz(archive_file, folder)
        shutil.copy2(archive_file, dest_dir)
    else:
        common.copy_build_directory(folder, os.path.join(dest_dir, folder_name))


def pg_macros(xml_source, pub_file, stringparams, dest_dir):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "support", "pretext-pg-macros.xsl")
    common.xsltproc(extraction_xslt, xml_source, None, output_dir=dest_dir, stringparams=stringparams)
