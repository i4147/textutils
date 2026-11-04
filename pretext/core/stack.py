import logging

log = logging.getLogger("ptxlogger")

import os
import os.path
import re

from . import common

__module_warning = common.__module_warning


_stack_tag_map = {
    "b": "alert",
    "strong": "alert",
    "i": "em",
    "code": "c",
    "tt": "c",
    "table": "tabular",
    "tr": "row",
    "td": "cell",
    "th": "cell",
    "a": "url",
}


def _stack_replace_latex(text):

    def process_match(match):
        has_asterisk = match.group(2) == "*"
        content = match.group(3).strip().replace("&", r"\amp ")

        lines = [line.strip() for line in content.split(r"\\") if line.strip()]
        xml_rows = "\n".join([f"<mrow>{line}</mrow>" for line in lines])

        opening_tag = '<md number="yes">' if has_asterisk else "<md>"
        return f"{opening_tag}\n{xml_rows}\n</md>"

    pattern = r"\\[\[\(]\s*\\begin\{(align|gather|eqnarray|multline)(\*?)\}(.*?)\\end\{\1\2\}\s*\\[\]\)]"
    text = re.sub(pattern, process_match, text, flags=re.DOTALL)

    text = re.sub(r"\\\((.*?[^\\])\\\)", r"<m>\1</m>", text, flags=re.DOTALL)
    text = re.sub(r"\\\[(.*?[^\\])\\]", r"<me>\1</me>", text, flags=re.DOTALL)

    return text


def _stack_replace_tags(text, asset_prefix_rel, mathmode=False):
    if not text.strip():
        return text
    text = text.replace("&nbsp;", "<nbsp/>")

    import lxml.html

    tree = lxml.html.fragment_fromstring(text, create_parent="p")
    for img in tree.xpath("//img"):
        img.tag = "image"
        if "src" in img.attrib:
            src = img.attrib.pop("src")
            new_src = f"{asset_prefix_rel}-{src}"
            if src.endswith(".svg"):
                new_src = new_src.replace(".svg", ".pdf")
            img.attrib["pi:generated"] = new_src
            img.attrib["xmlns:pi"] = "http://pretextbook.org/2020/pretext/internal"
        if "width" in img.attrib and not "%" in img.attrib["width"]:
            img.attrib["width"] = f"{int(img.attrib['width']) // 6}%"
        if "height" in img.attrib:
            img.attrib.pop("height")
    for tag, replacement in _stack_tag_map.items():
        for elem in tree.xpath(f"//{tag}"):
            elem.tag = replacement
    for elem in tree.xpath("//thead|//tbody"):
        elem.drop_tag()

    new_text = lxml.html.tostring(tree, encoding="unicode", method="xml")
    if mathmode:
        new_text = new_text.removeprefix("<p>").removesuffix("</p>")
    return new_text


def _stack_postprocess(text, asset_prefix_rel):
    text = _stack_replace_latex(text)
    return _stack_replace_tags(text, asset_prefix_rel)


def _stack_download_assets(assets, api_url, asset_prefix_abs, stack_file):
    import requests

    try:
        import fitz
    except ImportError:
        raise ImportError(__module_warning.format("pyMuPDF"))

    for filename, urlname in assets.items():
        plot_php_url = api_url.replace("/render", "/plot.php")
        full_url = "{}/{}".format(plot_php_url, urlname)
        response = requests.get(full_url)
        if response.status_code != 200:
            plots_url = api_url.replace("/render", "/plots")
            full_url = "{}/{}".format(plots_url, urlname)
            response = requests.get(full_url)
        if response.status_code == 200:
            response.raw.decode_content = True
            asset_file = "{}-{}".format(asset_prefix_abs, filename)
            log.debug("Extracting asset {} from {}.".format(asset_file, stack_file))
            if asset_file.endswith(".svg"):
                with open(asset_file, "wb") as svgout:
                    svgout.write(response.content)
                with fitz.Document(stream=response.content) as doc:
                    log.info("converting {} to PDF".format(asset_file))
                    pdfbytes = doc.convert_to_pdf()
                    asset_file_pdf = asset_file.replace(".svg", ".pdf")
                    with open(asset_file_pdf, "wb") as pdfout:
                        pdfout.write(pdfbytes)

                    log.info("converting {} to PNG".format(asset_file))
                    png = doc.load_page(0).get_pixmap(dpi=300, alpha=True)
                    asset_file_png = asset_file.replace(".svg", ".png")
                    png.save(asset_file_png)
            else:
                with open(asset_file, "wb") as f:
                    f.write(response.content)
        else:
            log.warning("Failed to download image {} for {}.".format(filename, stack_file))


def _stack_process_response(qdict, asset_prefix_rel, stack_file, base_url):
    if "isinteractive" not in qdict:
        log.warning(f"An error occurred while processing {stack_file}: {qdict.get('message')}")
        return "<statement><p>An error occurred while processing this question.</p></statement>"
    if qdict["isinteractive"]:
        log.warning(f"{stack_file} contains interactive elements")
        message = "<p>This question contains interactive elements.</p>"
        if base_url:
            message += (
                f'\n<p>Browse the <url href="{base_url}">online version of this book</url> to view this question.</p>'
            )
        return f"<statement>\n{message}\n</statement>"
    qtext = qdict["questionrender"]
    soltext = qdict["questionsamplesolutiontext"]

    qtext = re.sub(r"\[\[validation:(\w+)\]\]", "", qtext)
    qtext = re.sub(r"\[\[feedback:(\w+)\]\]", "", qtext)

    ansids = re.findall(r"\[\[input:(\w+)\]\]", qtext)
    answers = []
    for ansid in ansids:
        ansdata = qdict["questioninputs"][ansid]

        ansconfig = ansdata["configuration"]
        input_type = ansconfig["type"]
        answer = _stack_replace_tags(ansdata["samplesolutionrender"], asset_prefix_rel, mathmode=True)
        if input_type in ["algebraic", "numerical", "singlechar", "string", "units"] or input_type in [
            "equiv",
            "notes",
            "textarea",
            "varmatrix",
            "matrix",
        ]:
            if input_type == "singlechar":
                width = 1
            else:
                width = ansconfig["boxWidth"]
            input_render = f'<fillin characters="{width}" name="{ansid}"/>'
        elif input_type in ["checkbox", "radio", "dropdown"]:
            options = [opt_render for opt_id, opt_render in ansconfig["options"].items() if opt_id]
            if input_type == "dropdown":
                options_render = " | ".join(options)
                input_render = f"[ {options_render} ]"
            else:
                options_render = "\n".join(f"<li>{option}</li>" for option in options)
                input_render = f'<ol marker="(1)">\n{options_render}\n</ol>'
            if input_type == "checkbox":
                answer = ", ".join([f"({i})" for i in ansdata["samplesolution"].values()])
            elif input_type == "radio":
                answer = f"({ansdata['samplesolution']['']})"
            else:
                ans_id = ansdata["samplesolution"][""]
                answer = _stack_replace_tags(ansconfig["options"][ans_id], asset_prefix_rel, mathmode=True)
        elif input_type == "boolean":
            input_render = f"[ true | false ]"
        else:
            input_render = f"[[input:{ansid}]]"
            log.warning(f"{stack_file} contains unsupported input type")

        qtext = qtext.replace(f"[[input:{ansid}]]", input_render)
        if input_type not in ["singlechar", "notes", "dropdown"]:
            answer = f"<m>{answer}</m>"
        answers.append(f"<answer><p>{answer}</p></answer>")

    qtext = _stack_postprocess(qtext, asset_prefix_rel)
    soltext = _stack_postprocess(soltext, asset_prefix_rel)

    render_output = f"    <statement>{qtext}</statement>\n"
    if soltext:
        render_output += f"    <solution>{soltext}</solution>\n"
    if answers:
        render_output += "    " + "\n    ".join(answers)
    return render_output


def stack_extraction(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    import json
    import urllib

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    pub_vars = common.get_publisher_variable_report(xml_source, pub_file, stringparams)
    stack_server = common.get_publisher_variable(pub_vars, "stack-server")
    api_url = urllib.parse.urljoin(stack_server, "render")
    base_url = common.get_publisher_variable(pub_vars, "baseurl")
    log.info("Using STACK API server at {}".format(api_url))

    os.makedirs(dest_dir, exist_ok=True)
    msg = "converting STACK exercises from {} to static forms for placement in {}"
    log.info(msg.format(xml_source, dest_dir))

    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-stack.xsl")

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root

    log.info("extracting STACK exercises from {}".format(xml_source))
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))

    tmp_dir = common.get_temporary_directory()
    source_filename = os.path.join(tmp_dir, "stack-source.txt")
    log.debug("STACK source filenames temporarily in {}".format(source_filename))
    common.xsltproc(extraction_xslt, xml_source, source_filename, None, stringparams)

    generated_dir, external_dir = common.get_managed_directories(xml_source, pub_file)

    with open(source_filename, "r", encoding="utf-8") as source_file:
        for source in source_file:
            source, label = source.split()
            stack_file = os.path.join(external_dir, source)
            pretext_file = os.path.join(dest_dir, label + ".ptx")
            msg = 'converting STACK question file "{}" to static PreTeXt XML file "{}"'
            log.debug(msg.format(stack_file, pretext_file))

            asset_path = os.path.join(generated_dir, "stack", "images")
            os.makedirs(asset_path, exist_ok=True)
            asset_prefix_abs = os.path.join(asset_path, f"{label}")
            asset_prefix_rel = os.path.join("stack", "images", f"{label}")

            question_data = open(stack_file, encoding="utf-8").read()
            request_data = {"questionDefinition": question_data, "seed": None}
            question_json = requests.post(api_url, json=request_data)
            question_dict = json.loads(question_json.text)
            response = _stack_process_response(question_dict, asset_prefix_rel, stack_file, base_url)
            _stack_download_assets(question_dict.get("questionassets", {}), api_url, asset_prefix_abs, stack_file)
            wrap_response = "<stack-static>\n{}\n</stack-static>"
            question_pretext = wrap_response.format(response)

            with open(pretext_file, "w", encoding="utf-8") as ptxfile:
                ptxfile.write(question_pretext)
                ptxfile.close()
