#
#
#
#


import logging

log = logging.getLogger("ptxlogger")

import traceback


#
#   from foo import *
#   from foo import bar, baz
#
#   import foo
#   import foo as BAR
#
#
#
#

import os

import os.path

import shutil

import subprocess

import sys

import zipfile

import re

import contextlib

import time

import textwrap

#
#

#
#
#
from . import common

__module_warning = common.__module_warning
from . import webwork
from . import stack

try:
    import lxml.etree as ET
except ImportError:
    raise ImportError(__module_warning.format("lxml"))


#
#


def mathjax_latex(xml_source, pub_file, out_file, dest_dir, math_format, math_cross_references):
    import fileinput

    log.info("converting LaTeX from {} into {} format".format(xml_source, math_format))
    log.debug("converting LaTeX from {} into {} format".format(xml_source, math_format))

    extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "support/extract-math.xsl")
    cleaner_xslt = os.path.join(common.get_ptx_xsl_path(), "support/package-math.xsl")

    tmp_dir = common.get_temporary_directory()
    mjinput = os.path.join(tmp_dir, "mj-input-latex.html")
    mjintermediate = os.path.join(tmp_dir, "mj-intermediate.html")
    mjoutput = os.path.join(tmp_dir, "mj-output-{}.html".format(math_format))

    log.debug("temporary directory for MathJax work: {}".format(tmp_dir))
    log.debug("extracting LaTeX from {} and collected in {}".format(xml_source, mjinput))

    if math_format in ["svg", "mml", "kindle"]:
        punctuation = "display"
    elif math_format in ["nemeth", "speech"]:
        punctuation = "none"
    params = {}
    params["math.punctuation"] = punctuation
    if math_cross_references:
        params["math.cross-references"] = "yes"
    if pub_file:
        params["publisher"] = pub_file
    common.xsltproc(extraction_xslt, xml_source, mjinput, None, params)
    if math_format == "kindle":
        with fileinput.FileInput(mjinput, inplace=True, encoding="utf-8") as file:
            for line in file:
                print(line.replace(r"\(", r"\(\mathstrut "), end="")

    msg = "calling MathJax to convert LaTeX from {} into raw representations as {} in {}"
    log.debug(msg.format(mjinput, math_format, mjoutput))

    node_exec_cmd = common.get_executable_cmd("node")
    mjsre_page = os.path.join(common.get_ptx_path(), "script", "mjsre", "mj-sre-page.js")
    output = {
        "svg": "svg",
        "kindle": "mathml",
        "nemeth": "braille",
        "speech": "speech",
        "mml": "mathml",
    }
    try:
        mj_var = output[math_format]
    except KeyError:
        raise ValueError('PTX:ERROR: incorrect format ("{}") for MathJax conversion'.format(math_format))
    mj_option = "--" + mj_var
    mj_tag = "mj-" + mj_var
    mjpage_cmd = node_exec_cmd + [mjsre_page, mj_option, mjinput]
    with open(mjoutput, "w", encoding="utf-8") as outfile:
        subprocess.run(mjpage_cmd, stdout=outfile)

    orig = "&nbsp;"
    repl = " "
    xhtml_elt = re.compile(orig)
    with common.working_directory(tmp_dir):
        html_file = mjoutput
        with fileinput.FileInput(html_file, inplace=True, encoding="utf-8") as file:
            for line in file:
                print(xhtml_elt.sub(repl, line), end="")

    derivedname = common.get_output_filename(xml_source, out_file, dest_dir, "-" + math_format + ".xml")
    log.debug("packaging math as {} from {} into XML file {}".format(math_format, mjoutput, out_file))
    common.xsltproc(cleaner_xslt, mjoutput, derivedname)
    log.info("XML file of math representations deposited as {}".format(derivedname))


#
#


def prefigure_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, outformat, ext_converter):
    #
    import glob

    stringparams = stringparams.copy()

    msg = "converting PreFigure diagrams from {} to {} graphics for placement in {}"
    log.info(msg.format(xml_source, outformat.upper(), dest_dir))

    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-prefigure.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    log.info("extracting PreFigure diagrams from {}".format(xml_source))
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))

    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)

    with common.working_directory(tmp_dir):
        if outformat == "source" or outformat == "all":
            log.info("copying PreFigure source files into {}".format(dest_dir))
            shutil.copytree(tmp_dir, dest_dir, dirs_exist_ok=True)

        pf_source_files = os.listdir(tmp_dir)
        try:
            pf_source_files.remove("pf_publication.xml")
        except ValueError:
            pass

        _, external_dir = common.get_managed_directories(xml_source, pub_file)
        data_dir = common.get_source_directories(xml_source)
        common.copy_managed_directories(tmp_dir, external_abs=external_dir, data_abs=data_dir)

        if outformat == "all":
            os.mkdir("output")
            os.mkdir("output/tactile")

        for pfdiagram in pf_source_files:
            if ext_converter:
                ext_converter(pfdiagram, outformat, tmp_dir)
            else:
                individual_prefigure_conversion(pfdiagram, outformat)

        if os.path.exists("output"):
            log.info("copying PreFigure output to {}".format(dest_dir))
            shutil.copytree("output", dest_dir, dirs_exist_ok=True)


def individual_prefigure_conversion(pfdiagram, outformat):
    try:
        import prefig
    except ImportError:
        raise ImportError(__module_warning.format("prefig"))

    if outformat == "tactile" or outformat == "all":
        log.info("compiling PreFigure source file {} to tactile PDF".format(pfdiagram))
        prefig.engine.pdf("tactile", pfdiagram)
        pdf_name = pfdiagram[:-4] + ".pdf"
        shutil.move("output/" + pdf_name, "output/tactile/" + pdf_name)

    if outformat == "svg" or outformat == "all":
        log.info("compiling PreFigure source file {} to SVG".format(pfdiagram))
        prefig.engine.build("svg", pfdiagram)

    if outformat == "pdf" or outformat == "all":
        log.info("compiling PreFigure source file {} to PDF".format(pfdiagram))
        prefig.engine.pdf("svg", pfdiagram, dpi=100)

    if outformat == "png" or outformat == "all":
        log.info("compiling PreFigure source file {} to PNG".format(pfdiagram))
        prefig.engine.png("svg", pfdiagram)


def asymptote_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, outformat, method, ext_converter):
    #
    import glob

    stringparams = stringparams.copy()

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    msg = 'converting Asymptote diagrams from {} to {} graphics for placement in {} with method "{}"'
    log.info(msg.format(xml_source, outformat.upper(), dest_dir, method))

    if not (method in ["local", "server"]):
        raise ValueError("{} is not a method for Asymptote diagram generation".format(method))

    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-asymptote.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    log.info("extracting Asymptote diagrams from {}".format(xml_source))
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))
    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)
    with common.working_directory(tmp_dir):
        if outformat == "source" or outformat == "all":
            for asydiagram in os.listdir(tmp_dir):
                log.info("copying source file {}".format(asydiagram))
                shutil.copy2(asydiagram, dest_dir)
        if outformat == "all":
            outformats = ["html", "svg", "png", "pdf", "eps"]
        elif outformat in ["html", "svg", "png", "pdf", "eps"]:
            outformats = [outformat]
        else:
            outformats = []
        asy_executable_cmd = []
        asyversion = ""
        rendering_option = []
        if outformats and (method == "local"):
            asy_executable_cmd = common.get_executable_cmd("asy")
            proc = subprocess.Popen([asy_executable_cmd[0], "--version"], stderr=subprocess.PIPE)
            asyversion = proc.stderr.read().decode("ascii")[:-1]
            version_numbers = asymptote_version_numbers(asyversion)
            if version_numbers is None:
                msg = [
                    "the version of Asymptote could not be determined, so a current version",
                    "             is assumed and offscreen rendering requested.  If no images are built,",
                    "             and your Asymptote lies between 2.66 and 3.11, that is the explanation.",
                    "             A version query replied:",
                    "             {}".format(asyversion),
                ]
                log.warning("\n".join(msg))
                version_numbers = (3, 13)
            if ((2, 11) <= version_numbers < (2, 66)) or ((3, 12) <= version_numbers):
                rendering_option = ["-offscreen"]
            else:
                rendering_option = ["-iconify"]
        for outform in outformats:
            asy_cli = []
            alberta = ""
            if method == "local":
                asy_cli = asy_executable_cmd + ["-f", outform, "-noV"]
                if outform in ["pdf", "eps"]:
                    asy_cli += ["-noprc"] + rendering_option + ["-tex", "xelatex", "-batchMask"]
                elif outform in ["svg", "png"]:
                    asy_cli += ["-render=4", "-tex", "xelatex"] + rendering_option
            if method == "server":
                alberta = "http://asymptote.ualberta.ca:10007?f={}".format(outform)
            for asydiagram in glob.glob(os.path.join(tmp_dir, "*.asy")):
                if ext_converter:
                    ext_converter(asydiagram, outform, method, asy_cli, asyversion, alberta, dest_dir)
                else:
                    individual_asymptote_conversion(asydiagram, outform, method, asy_cli, asyversion, alberta, dest_dir)


def asymptote_version_numbers(version_banner):
    version_match = re.search(r"Asymptote version ([0-9]+(?:\.[0-9]+)*)", version_banner)
    if not version_match:
        return None
    return tuple(int(number) for number in version_match.group(1).split("."))


def individual_asymptote_conversion(asydiagram, outform, method, asy_cli, asyversion, alberta, dest_dir):
    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    filebase, _ = os.path.splitext(asydiagram)
    asyout = "{}.{}".format(filebase, outform)
    log.info("converting {} to {}".format(asydiagram, asyout))
    if method == "local":
        asy_cmd = asy_cli + [asydiagram]
        log.debug("asymptote conversion {}".format(asy_cmd))
        subprocess.call(asy_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if method == "server":
        log.debug("asymptote server query {}".format(alberta))
        with open(asydiagram, encoding="utf-8") as f:
            data = f.read().encode("utf-8")
            response = requests.post(url=alberta, data=data)
            open(asyout, "wb").write(response.content)
    if os.path.exists(asyout):
        shutil.copy2(asyout, dest_dir)
    else:
        msg = [
            "the Asymptote output {} was not built".format(asyout),
            "             Perhaps your code has errors (try testing in the Asymptote web app).",
        ]
        if method == "local":
            msg += [
                "             Or your local copy of Asymptote may be too old to build this format,",
                "             since not every version can produce every format.",
                "",
                "             Your Asymptote reports its version within the following:",
                "             {}".format(asyversion),
            ]
        log.warning("\n".join(msg))


def sage_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, outformat, ext_converter):

    #
    if outformat == "all":
        log.info('Pass 1 for "all" formats, now generating PDF')
        sage_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, "pdf", ext_converter)
        log.info('Pass 2 for "all" formats, now generating SVG')
        sage_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, "svg", ext_converter)
        log.info('Pass 3 for "all" formats, now generating PNG')
        sage_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, "png", ext_converter)
        log.info('Pass 4 for "all" formats, now generating HTML')
        sage_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, "html", ext_converter)
        return None
    log.info(
        "converting Sage diagrams from {} to {} graphics for placement in {}".format(
            xml_source, outformat.upper(), dest_dir
        )
    )
    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    sage_executable_cmd = common.get_executable_cmd("sage")
    log.debug("sage executable: {}".format(sage_executable_cmd[0]))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-sageplot.xsl")
    log.info("extracting Sage diagrams from {}".format(xml_source))
    stringparams["sageplot.fileformat"] = outformat
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)
    with common.working_directory(tmp_dir):
        failed_images = []
        for sageplot in os.listdir(tmp_dir):
            try:
                if ext_converter:
                    ext_converter(sageplot, outformat, dest_dir, sage_executable_cmd)
                else:
                    individual_sage_conversion(sageplot, outformat, dest_dir, sage_executable_cmd)
            except Exception as e:
                failed_images.append(sageplot)
                log.warning(e)
    if failed_images:
        msg = "\n".join([
            "Sage conversion failed for {} sageplot(s).",
            "Build with '-v debug' option and review the log for error messages.",
            "Images are:",
        ]).format(len(failed_images))
        image_list = "\n  " + "\n  ".join(failed_images)
        raise ValueError(msg + image_list)


def individual_sage_conversion(sageplot, outformat, dest_dir, sage_executable_cmd):
    filebase, _ = os.path.splitext(sageplot)
    sageout = "{0}.{1}".format(filebase, outformat)
    sage_cmd = sage_executable_cmd + [sageplot]
    log.info("converting {} to {}".format(sageplot, sageout))
    log.debug("sage conversion {}".format(sage_cmd))

    result = subprocess.run(sage_cmd, capture_output=True, encoding="utf-8")
    if result.returncode:
        log.debug(result.stderr)
        raise Exception("sage conversion of {} failed".format(sageplot))
    else:
        shutil.copy2(sageout, dest_dir)


def latex_image_conversion(xml_source, pub_file, stringparams, xmlid_root, dest_dir, outformat, method, ext_converter):

    stringparams = stringparams.copy()

    log.info(
        "converting latex-image pictures from {} to {} graphics for placement in {}".format(
            xml_source, outformat, dest_dir
        )
    )
    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory for latex-image conversion: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    log.info("extracting latex-image pictures from {}".format(xml_source))
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))
    _, external_dir = common.get_managed_directories(xml_source, pub_file)
    data_dir = common.get_source_directories(xml_source)
    common.copy_managed_directories(tmp_dir, external_abs=external_dir, data_abs=data_dir)
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-latex-image.xsl")
    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)
    with common.working_directory(tmp_dir):
        failed_images = []
        files = list(filter(os.path.isfile, os.listdir(tmp_dir)))
        for latex_image in files:
            try:
                if ext_converter:
                    ext_converter(latex_image, outformat, dest_dir, method)
                else:
                    individual_latex_image_conversion(latex_image, outformat, dest_dir, method)
            except ImportError:
                raise
            except Exception as e:
                failed_images.append(latex_image)
                log.warning(e)

    if failed_images:
        msg = "\n".join([
            'LaTeX compilation failed for {} "latex-image"(s).',
            "Review the log for error messages, and LaTeX transcripts.",
            "Images are:",
        ]).format(len(failed_images))
        image_list = "\n  " + "\n  ".join(failed_images)
        raise ValueError(msg + image_list)


def individual_latex_image_conversion(latex_image, outformat, dest_dir, method):
    try:
        import pdfCropMargins
    except ImportError:
        raise ImportError(__module_warning.format("pdfCropMargins"))
    try:
        import fitz
    except ImportError:
        raise ImportError(__module_warning.format("pyMuPDF"))

    if outformat == "source":
        shutil.copy2(latex_image, dest_dir)
        log.info("copying {} to {}".format(latex_image, dest_dir))
    else:
        filebase, _ = os.path.splitext(latex_image)
        latex_image_pdf = "{}.pdf".format(filebase)
        latex_image_svg = "{}.svg".format(filebase)
        latex_image_png = "{}.png".format(filebase)
        latex_image_eps = "{}.eps".format(filebase)
        latex_image_log = "{}.log".format(filebase)
        latex_key = common.get_deprecated_tex_fallback(method)
        tex_executable_cmd = common.get_executable_cmd(latex_key)
        log.debug("tex executable: {}".format(tex_executable_cmd[0]))
        latex_cmd = tex_executable_cmd + ["-interaction=nonstopmode", "-halt-on-error", latex_image]
        log.info("converting {} to {}".format(latex_image, latex_image_pdf))
        result = _latex_compile(latex_cmd, latex_image_log, latex_image, capture_output=True)

        if result.returncode != 0:
            msg = "\n".join([
                "LaTeX compilation of {} failed.",
                'Re-run, requesting "source" as the format, to analyze the image.',
                "Likely creating the entire document as PDF will fail similarly.",
                "The transcript of the LaTeX run follows.",
            ]).format(latex_image)
            log.error(msg)
            log.debug(result.stdout)
            raise Exception("LaTeX compilation of {} failed".format(latex_image))
        else:
            pcm_cmd = [
                latex_image_pdf,
                "-o",
                "cropped-" + latex_image_pdf,
                "-t",
                "254",
                "-p",
                "0",
                "-a",
                "-1",
            ]
            log.info("cropping {} to {}".format(latex_image_pdf, "cropped-" + latex_image_pdf))
            pdfCropMargins.crop(pcm_cmd)
            if not os.path.exists("cropped-" + latex_image_pdf):
                log.error(
                    "There was a problem cropping {} and {} was not created".format(
                        latex_image_pdf, "cropped-" + latex_image_pdf
                    )
                )
            shutil.move("cropped-" + latex_image_pdf, latex_image_pdf)
            log.info("renaming {} to {}".format("cropped-" + latex_image_pdf, latex_image_pdf))
            if outformat == "all":
                shutil.copy2(latex_image, dest_dir)
            if outformat == "pdf" or outformat == "all":
                shutil.copy2(latex_image_pdf, dest_dir)
            if outformat == "svg" or outformat == "all":
                log.info("converting {} to {}".format(latex_image_pdf, latex_image_svg))
                with fitz.Document(latex_image_pdf) as doc:
                    svg = doc.load_page(0).get_svg_image()
                with open(latex_image_svg, "w", encoding="utf-8") as f:
                    f.write(svg)

                if not os.path.exists(latex_image_svg):
                    log.error(
                        "There was a problem converting {} to svg and {} was not created".format(
                            latex_image_pdf, latex_image_svg
                        )
                    )
                shutil.copy2(latex_image_svg, dest_dir)
            if outformat == "png" or outformat == "all":
                log.info("converting {} to {}".format(latex_image_pdf, latex_image_png))
                with fitz.Document(latex_image_pdf) as doc:
                    png = doc.load_page(0).get_pixmap(dpi=300, alpha=True)
                png.save(latex_image_png)
                shutil.copy2(latex_image_png, dest_dir)

                if not os.path.exists(latex_image_png):
                    log.error(
                        "There was a problem converting {} to png and {} was not created".format(
                            latex_image_pdf, latex_image_png
                        )
                    )
                shutil.copy2(latex_image_png, dest_dir)
            if outformat == "eps" or outformat == "all":
                pdfeps_executable_cmd = common.get_executable_cmd("pdfeps")
                log.debug("pdfeps executable: {}".format(pdfeps_executable_cmd[0]))
                eps_cmd = pdfeps_executable_cmd + [
                    "-eps",
                    latex_image_pdf,
                    latex_image_eps,
                ]
                log.info("converting {} to {}".format(latex_image_pdf, latex_image_eps))
                subprocess.call(eps_cmd)
                if not os.path.exists(latex_image_eps):
                    log.error(
                        "There was a problem converting {} to eps and {} was not created".format(
                            latex_image_pdf, latex_image_eps
                        )
                    )
                shutil.copy2(latex_image_eps, dest_dir)


#
#


def datafiles_to_xml(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    stringparams = stringparams.copy()

    import base64

    msg = "converting data files from {} to text representations in XML files for placement in {}"
    log.info(msg.format(xml_source, dest_dir))

    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-datafile.xsl")
    the_files = os.path.join(tmp_dir, "datafile-list.txt")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    log.info("extracting source files from {}".format(xml_source))
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))
    common.xsltproc(extraction_xslt, xml_source, the_files, None, stringparams)

    generated_abs, external_abs = common.get_managed_directories(xml_source, pub_file)

    image_info = (
        '<pi:image-b64 xmlns:pi="http://pretextbook.org/2020/pretext/internal" pi:mime-type="{}" pi:base64="{}"/>'
    )
    text_info = '<pi:text-file xmlns:pi="http://pretextbook.org/2020/pretext/internal">{}</pi:text-file>'

    with open(the_files, "r", encoding="utf-8") as datafile_list:
        dfs = datafile_list.readlines()
    for df in dfs:
        visible_id, file_type, relative_path = df.split()
        data_file = os.path.join(external_abs, relative_path)
        log.debug("converting data file {} to a text/XML file".format(data_file))

        if file_type == "image":
            _, extension = os.path.splitext(data_file)
            lcext = extension[1:].lower()
            if lcext in ["jpeg", "jpg"]:
                mime_type = "image/jpeg"
            elif lcext == "png":
                mime_type = "image/png"
            elif lcext == "gif":
                mime_type = "image/gif"
            elif lcext == "webp":
                mime_type = "image/webp"
            elif lcext == "avif":
                mime_type = "image/avif"
            elif lcext == "apng":
                mime_type = "image/apng"
            elif lcext == "svg":
                mime_type = "image/svg+xml"
            else:
                log.info("PTX:WARNING : MIME type of image {} not determined".format(data_file))
                mime_type = "unknown"

            with open(data_file, "rb") as f:
                base64version = base64.b64encode(f.read()).decode("utf8")
            xml_representation = image_info.format(mime_type, base64version)
        elif file_type == "pre":
            with open(data_file, "rb") as f:
                rawtext = f.read().decode("utf8")
            xml_representation = text_info.format(rawtext)
        else:
            xml_representation = "<oops/>"

        out_filename = os.path.join(dest_dir, visible_id + ".xml")
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(__xml_header)
            f.write(xml_representation)


#
#


def latex_tactile_image_conversion(xml_source, pub_file, stringparams, dest_dir, outformat):

    msg = "\n".join([
        'Support for production of "latex-image" as tactile',
        "graphics with braille labels was discontinued on 2024-07-29.",
        "Instead, investigate the PreFigure project at prefigure.org.",
    ])
    raise ValueError(msg)


def tracer(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    stringparams = stringparams.copy()

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    url_string = "http://tracer.runestone.academy:5000/trace{}"
    server_error_msg = "\n".join([
        "the server at {} could not process program source file {}.",
        "No trace file was produced.  The generated traceback follows, other files will still be processed.",
    ])

    log.info("creating trace data from {} for placement in {}".format(xml_source, dest_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-trace.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    tmp_dir = common.get_temporary_directory()
    code_filename = os.path.join(tmp_dir, "codelens.txt")
    log.debug("Program sources for traces temporarily in {}".format(code_filename))
    common.xsltproc(extraction_xslt, xml_source, code_filename, None, stringparams)
    with open(code_filename, "r", encoding="utf-8") as code_file:
        contents = code_file.read().rstrip()

    if contents == "":
        log.info("no traces found to generate in {}".format(code_filename))
        return

    program_groups = contents.split("!end_codelens_trace_group!")
    program_groups.pop()
    for program_group in program_groups:
        lines = program_group.split("\n")
        visible_id = lines[0]
        runestone_id = lines[1]
        if runestone_id.strip() == "":
            log.error(
                "No runestone_id found for visible_id {}. Codelens must have a label or be the child of exercise like element with a label.".format(
                    visible_id
                )
            )
            continue
        trace_filename = lines[2]
        language = lines[3]
        source = lines[4]
        starting_instruction = int(lines[5])
        questions = lines[6:]

        if language == "python":
            url = url_string.format("py")
        else:
            url = url_string.format(language)
        source = source.replace("\\n", "\n")
        log.info("converting {} source {} to tracefile {}...".format(language, visible_id, trace_filename))

        trace = ""
        if (language == "c") or (language == "cpp"):
            try:
                r = requests.post(url, data=dict(src=source), timeout=30)
                if r.status_code == 200:
                    trace = r.text[r.text.find('{"code":') :]
            except Exception as e:
                log.debug(traceback.format_exc())
                log.error(server_error_msg.format(url, visible_id))
        elif language == "java":
            try:
                r = requests.post(url, data=dict(src=source), timeout=30)
                if r.status_code == 200:
                    trace = r.text
            except Exception as e:
                log.debug(traceback.format_exc())
                log.error(server_error_msg.format(url, visible_id))
        elif language == "python":
            try:
                r = requests.post(url, data=dict(src=source), timeout=30)
                if r.status_code == 200:
                    trace = r.text
            except Exception as e:
                log.debug(traceback.format_exc())
                log.error(server_error_msg.format(url, visible_id))

        if trace:
            import json

            trace_dict = json.loads(trace)
            trace_dict["startingInstruction"] = starting_instruction
            if questions:
                trace_steps = trace_dict.get("trace")
                for question in questions:
                    if question.strip() == "":
                        continue
                    question_line, answer_raw, feedback, prompt = question.split(":||:")
                    question_line = int(question_line)
                    answer_type, answer_value = answer_raw.split("-", 2)
                    question_dict = {
                        "text": prompt,
                        ("correctText" if answer_type == "literal" else "correct"): answer_value,
                    }
                    if feedback:
                        question_dict["feedback"] = feedback

                    for trace_step in trace_steps:
                        if trace_step["line"] == question_line and trace_step["event"] == "step_line":
                            trace_step["question"] = question_dict
            trace = json.dumps(trace_dict)

            script_template = """
                if (allTraceData === undefined) {{
                    var allTraceData = {{}};
                }}
                (function() {{ // IIFE to avoid variable collision
                    let codelensID = "{}";  //fallback
                    let partnerCodelens = document.currentScript.parentElement.querySelector(".pytutorVisualizer");
                    if (partnerCodelens) {{
                        codelensID = partnerCodelens.id;
                    }}
                    allTraceData[codelensID] = {};
                }})();"""
            script_template = textwrap.dedent(script_template)
            trace = script_template.format(runestone_id, trace.rstrip())
            trace_file = os.path.join(dest_dir, trace_filename)
            with open(trace_file, "w", encoding="utf-8") as f:
                f.write(trace)


#
#
def dynamic_substitutions(xml_source, pub_file, stringparams, xmlid_root, dest_dir, ext_rs_methods):
    ptx_dir = common.get_ptx_path()
    ptx_xsl_dir = common.get_ptx_xsl_path()
    node_exec_cmd = common.get_executable_cmd("node")
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-dynamic.xsl")
    script = os.path.join(ptx_dir, "script", "dynsub", "dynamic_extract.mjs")
    dyn_subs_file = os.path.join(dest_dir, "dynamic_substitutions.xml")

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    stringparams["host-platform"] = "web"

    tmp_dir = common.get_temporary_directory()
    json_file = os.path.join(tmp_dir, "dynamic-setup.json")
    log.info("Creating temporary dynamic exercise setup JSON: {}".format(json_file))
    common.xsltproc(extraction_xslt, xml_source, json_file, tmp_dir, stringparams)

    import json

    external_directory_prefix = "external/"
    with open(json_file, encoding="utf-8") as f:
        dynamic_setup = json.load(f)
    local_libraries = set()
    for exercise in dynamic_setup.get("exercises", []):
        for specifier in exercise.get("exercise_imports", []):
            if specifier.startswith(external_directory_prefix):
                local_libraries.add(specifier[len(external_directory_prefix) :])

    _, external_dir = common.get_managed_directories(xml_source, pub_file)
    common.copy_managed_resources(tmp_dir, external_abs=external_dir, external_resources=local_libraries)

    log.info("Generating substitutions.")
    import subprocess

    try:
        result = subprocess.run(
            node_exec_cmd
            + [
                script,
                "--input={}".format(json_file),
                "--output={}".format(dyn_subs_file),
                "--basedir={}".format(tmp_dir),
            ],
            capture_output=True,
            text=True,
        )
    except Exception as e:
        root_cause = str(e)
        msg = "PTX:ERROR:   There was a problem generating dynamic substitutions.\n"
        raise ValueError(msg + root_cause)

    #
    #
    for line in result.stderr.splitlines():
        if not line.strip():
            continue
        common.log_relayed_message(line)
    if result.returncode == 1:
        log.error(
            "Some dynamic substitutions could not be generated.  The "
            'affected exercises will read "[ERROR generating substitution]" in '
            "static output.  See the messages above."
        )
    elif result.returncode != 0:
        raise ValueError(
            "PTX:ERROR:   The dynamic substitution script failed and no substitutions "
            "were generated.  Exercises with dynamic content will be missing from "
            "static output.  See the messages above."
        )


#
#


#
#


#
#


#
#


def _pretextify(biblio):

    biblio = re.sub(r"<i>", r"<pi:italic>", biblio)
    biblio = re.sub(r"</i>", r"</pi:italic>", biblio)
    biblio = re.sub(r"<b>", r"<pi:bold>", biblio)
    biblio = re.sub(r"</b>", r"</pi:bold>", biblio)
    biblio = re.sub("\u2013", r"<ndash/>", biblio)
    biblio = re.sub("\u201c", r"<lq/>", biblio)
    biblio = re.sub("\u201d", r"<rq/>", biblio)

    return biblio


def references(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    #

    pub_vars = common.get_publisher_variable_report(xml_source, pub_file, stringparams)
    csl_style = common.get_publisher_variable(pub_vars, "csl-style-file")
    using_csl_styles = common.get_publisher_variable(pub_vars, "b-using-csl-styles")

    if using_csl_styles == "false":
        msg = " ".join([
            "requesting formatted references and citations is not possible",
            "without a CSL style file specified in the publication file.",
            "No action is being taken.",
        ])
        log.error(msg)
        return

    #
    import json

    import citeproc.source.json
    import citeproc

    XML = "http://www.w3.org/XML/1998/namespace"
    PI = "http://pretextbook.org/2020/pretext/internal"
    CSL = "http://purl.org/net/xbiblio/csl"
    NSMAP = {"xml": XML, "pi": PI, "cs": CSL}

    def warn(citation_item):
        log.warning("PTX:WARNING: Reference with key '{}' not found in the bibliography.".format(citation_item.key))

    #

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-biblio-csl.xsl")

    tmp_dir = common.get_temporary_directory()
    biblio_xml = os.path.join(tmp_dir, "biblio-csl.xml")

    common.xsltproc(extraction_xslt, xml_source, biblio_xml, None, stringparams)

    biblio_tree = ET.parse(biblio_xml)

    #

    style = citeproc.CitationStylesStyle(csl_style, validate=False)

    #
    # style_layout = style.xml.xpath("/cs:style/cs:citation/cs:layout", namespaces=NSMAP)[0]
    # citation_punct = style_layout.attrib
    # if "prefix" in citation_punct:
    #     prefix = citation_punct["prefix"]
    # else:
    #     prefix = ""

    style_class = style.root.get("class")
    if not (style_class in ["in-text", "note"]):
        msg = " ".join([
            'The requested CSL style file ("{}") has a /style/@class',
            'attribute value ("{}") we do not recognize.',
            "No action is being taken.",
        ])
        log.error(msg.format(csl_style, style_class))
        return
    if style_class == "note":
        msg = " ".join([
            'The requested CSL style file ("{}") uses a footnote/endnote',
            "style for citations, which PreTeXt does not yet support.",
            "No action is being taken.",
        ])
        log.error(msg.format(csl_style))
        return

    style_citation_format = style.root.info.category.get("citation-format")
    if not (style_citation_format in ["numeric", "author-date", "note"]):
        msg = " ".join([
            'The requested CSL style file ("{}") has a/style/info/category/@citation-format',
            'attribute value ("{}") we do not recognize.',
            "No action is being taken.",
        ])
        log.error(msg.format(csl_style, style_citation_format))
        return
    is_numeric = style_citation_format == "numeric"

    """
    Typical CSL XML structure for the suffix used with numeric
    identification, for example
        "6. "    ->  ". "
        "[6]"    ->  "]"
        "(6)  "  ->  ")  "

    <bibliography entry-spacing="0" second-field-align="flush">
        <layout suffix=".">
            <text variable="citation-number" prefix="[" suffix="]"/>
    """

    numeric_suffix = None
    if is_numeric:
        layout_element = style.xml.xpath(
            "/cs:style/cs:bibliography/cs:layout/cs:text[@variable = 'citation-number']", namespaces=NSMAP
        )[0]
        numeric_suffix = layout_element.get("suffix")

    #

    references_blob = biblio_tree.xpath("/pi:pretext-biblio-csl/pi:biblio-csl", namespaces=NSMAP)
    json_raw = references_blob[0].text
    json_parsed = json.loads(json_raw)
    references_source = citeproc.source.json.CiteProcJSON(json_parsed)
    references = citeproc.CitationStylesBibliography(style, references_source, citeproc.formatter.html)

    #

    citation_xref = biblio_tree.xpath("/pi:pretext-biblio-csl/pi:xref-csl", namespaces=NSMAP)

    xref_ids = [c.attrib["id"] for c in citation_xref]

    xref_refs = [c.text.split() for c in citation_xref]

    citeproc_citations = []
    for ref_list in xref_refs:
        citeproc_citation_items = []
        for ref in ref_list:
            citeproc_citation_items.append(citeproc.CitationItem(ref))
        citeproc_citation = citeproc.Citation(citeproc_citation_items)
        citeproc_citations.append(citeproc_citation)
        references.register(citeproc_citation)

    #

    references.sort()
    references_formatted = [_pretextify(str(item)) for item in references.bibliography()]

    references_wrapped = []
    biblio_pattern = '<pi:csl-biblio numeric="{}" xml:id="{}" xmlns:{}="{}">{}</pi:csl-biblio>'
    for k, rf in zip(references.keys, references_formatted):
        numeric = ""
        if numeric_suffix:
            numeric, rf = rf.split(numeric_suffix, 1)
            numeric = numeric + numeric_suffix

        references_wrapped.append(biblio_pattern.format(numeric, k, "pi", PI, rf))

    #

    #
    #
    #
    #
    #

    rare = "P1zXvPN5SACeY"

    layout = style.root.citation.layout
    prefix = layout.get("prefix", "")
    real_delimiter = layout.get("delimiter", "")
    suffix = layout.get("suffix", "")
    layout.set("delimiter", rare)

    citation = style.root.citation
    sorter = citation.sort

    citations_wrapped = []
    solo_xref_pattern = '<xref ref="{}" pi:custom-text="yes" xmlns:{}="{}">{}</xref>'
    citation_pattern = '<pi:csl-citation xml:id="{}" xmlns:{}="{}">{}</pi:csl-citation>'
    for c, xref_id in zip(citeproc_citations, xref_ids):
        rough = references.cite(c, warn)
        rough = rough[len(prefix) : -len(suffix)]
        rough = rough.split(rare)

        cites = c.cites
        cites.sort(key=lambda x: references.keys.index(x.key))
        if sorter is not None:
            cites = sorter.sort(cites, layout)
        one_citation = []
        for text_cite, cite_cite in zip(rough, cites):
            ptx_cite = solo_xref_pattern.format(cite_cite.key, "pi", PI, text_cite)
            one_citation.append(ptx_cite)
        a_cite = _pretextify(prefix + real_delimiter.join(one_citation) + suffix)
        a_cite = citation_pattern.format(xref_id, "pi", PI, a_cite)
        citations_wrapped.append(a_cite)

    #

    csl_references = ET.Element(ET.QName(NSMAP["pi"], "csl-references"), nsmap=NSMAP)
    csl_references.set("csl-style-file", csl_style)

    index = 1
    for rw in references_wrapped:
        biblio_tree = ET.fromstring(rw)
        csl_references.insert(index, biblio_tree)
        index = index + 1
    for cw in citations_wrapped:
        xref_tree = ET.fromstring(cw)
        csl_references.insert(index, xref_tree)
        index = index + 1

    bib_file = os.path.join(dest_dir, "csl-bibliography.xml")

    try:
        with open(bib_file, "wb") as f:
            f.write(ET.tostring(csl_references, encoding="utf-8", xml_declaration=True, pretty_print=True))
    except Exception as e:
        root_cause = str(e)
        msg = "PTX:ERROR: there was a problem writing a references file: {}\n"
        raise ValueError(msg.format(f) + root_cause)


#
#


def gd_pack(source_dir, dest_zip_file, pack_name, version):

    try:
        from . import godot_helper
    except ImportError:
        raise ImportError(__module_warning.format("godot_helper"))

    source_path = os.path.realpath(source_dir)
    try:
        godot_cmd = common.get_executable_cmd("godot")
    except Exception as e:
        log.info("{}".format(e))
        godot_cmd = "godot"

    godot_cmd = godot_helper.resolve_godot(godot_cmd, version)
    godot_helper.ensure_export_templates(version)

    PROJECT_FILENAME = "project.godot"
    EXPORTS_FILENAME = "export_presets.cfg"
    EXPORT_FILENAME = "export_preset.cfg"
    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory for Godot pack build: {}".format(tmp_dir))
    shutil.copytree(source_path, tmp_dir, dirs_exist_ok=True)

    source_config_path = os.path.join(tmp_dir, "practice_solutions", pack_name, EXPORT_FILENAME)

    target_config_path = os.path.join(tmp_dir, EXPORTS_FILENAME)
    target_project_path = os.path.join(tmp_dir, PROJECT_FILENAME)

    godot_template_path = os.path.join(get_ptx_path(), "pretext", "lib", "godot")
    template_project_path = os.path.join(godot_template_path, PROJECT_FILENAME)
    shutil.copy2(source_config_path, target_config_path)
    shutil.copy2(template_project_path, target_project_path)

    command = [godot_cmd, "--headless", "--path", tmp_dir, "--editor", "--quit"]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        log.info("Trial successful!")
        log.info(result.stdout)
        log.info(result.stderr)
    else:
        log.error("Trial failed. Godot Output:")
        log.error(result.stdout)
        log.error(result.stderr)
        raise OSError(result.stderr)
    command = [godot_cmd, "--headless", "--path", tmp_dir, "--export-pack", pack_name, dest_zip_file]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        log.info("Export successful! File saved to: {}".format(dest_zip_file))
        log.info(result.stdout)
        log.info(result.stderr)
    else:
        log.error("Export failed. Godot Output:")
        log.error(result.stdout)
        log.error(result.stderr)
        raise OSError(result.stderr)


def gdscript_pck(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    stringparams = stringparams.copy()
    source_dir = common.get_source_path(xml_source)
    log.info("exporting GDScript interactives from {} for placement in {}".format(source_dir, dest_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-gdscript.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    tmp_dir = common.get_temporary_directory()
    id_filename = os.path.join(tmp_dir, "gdscript-ids.txt")
    log.debug("GDScript id list temporarily in {}".format(id_filename))
    common.xsltproc(extraction_xslt, xml_source, id_filename, None, stringparams)
    with open(id_filename, "r") as id_file:
        quads = [p.strip() for p in id_file.readlines() if "," in p]
    for quad in quads:
        src = path = name = version = None
        try:
            quad_a = quad.split(",")
            src = os.path.join(source_dir, quad_a[1])
            path = os.path.join(dest_dir, quad_a[0] + ".zip")
            parts = quad_a[2].split("/")
            name = parts[-2]
            version = quad_a[3]
            log.info("exporting {} as {} using {} ...".format(src, path, name))
            gd_pack(src, path, name, version)
        except Exception as e:
            log.error(
                "GDScript pack export failed for quad {} (src={}, dest={}, pack_name={}, version={}): {}: {}".format(
                    quad, src, path, name, version, type(e).__name__, e
                )
            )
            log.debug(traceback.format_exc())

    log.info("GDScript pck exporting complete")


#
#


def youtube_thumbnail(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    stringparams = stringparams.copy()

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    log.info("downloading YouTube thumbnails from {} for placement in {}".format(xml_source, dest_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-youtube.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    tmp_dir = common.get_temporary_directory()
    id_filename = os.path.join(tmp_dir, "youtube-ids.txt")
    log.debug("YouTube id list temporarily in {}".format(id_filename))
    common.xsltproc(extraction_xslt, xml_source, id_filename, None, stringparams)
    with open(id_filename, "r", encoding="utf-8") as id_file:
        thumbs = [t.strip() for t in id_file.readlines() if "," in t]

    failed_thumbnails = []
    for thumb in thumbs:
        thumb_pair = thumb.split(",")
        url = "http://i.ytimg.com/vi/{}/default.jpg".format(thumb_pair[0])
        path = os.path.join(dest_dir, thumb_pair[1] + ".jpg")
        log.info("downloading {} as {}...".format(url, path))
        try:
            r = requests.get(url, stream=True, timeout=10)
        except requests.exceptions.RequestException as e:
            failed_thumbnails.append(url)
            log.warning("the download of {} failed: {}".format(url, e))
            continue
        if r.status_code == 200:
            with open(path, "wb") as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            failed_thumbnails.append(url)
            log.warning("the download of {} returned a bad status code ({})".format(url, r.status_code))
    if failed_thumbnails:
        msg = "\n".join([
            "{} YouTube thumbnail(s) failed to download.",
            "Perhaps a video has gone missing; try the address(es) manually:",
        ]).format(len(failed_thumbnails))
        url_list = "\n  " + "\n  ".join(failed_thumbnails)
        raise OSError(msg + url_list)
    log.info("YouTube thumbnail download complete")


#
#


def play_button(dest_dir):

    ptx_xsl_dir = common.get_ptx_xsl_path()
    play_button_provided_image = os.path.join(ptx_xsl_dir, "support", "play-button", "play-button.png")
    log.info('Generating generic video preview, aka "play button" into {}'.format(dest_dir))
    shutil.copy2(play_button_provided_image, dest_dir)


#
#


def qrcode(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    stringparams = stringparams.copy()

    has_image = False
    try:
        pub_vars = common.get_publisher_variable_report(xml_source, pub_file, stringparams)
        image = common.get_publisher_variable(pub_vars, "qrcode-image")
        _, external_dir = common.get_managed_directories(xml_source, pub_file)
        image_path = os.path.join(external_dir, image)
        if image != "" and os.path.exists(image_path):
            has_image = True
    except:
        pass

    try:
        import qrcode
    except ImportError:
        raise ImportError(__module_warning.format("qrcode"))

    import qrcode.image.styledpil

    log.info("manufacturing QR codes from {} for placement in {}".format(xml_source, dest_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-qrcode.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    import xml.etree.ElementTree as ET

    pi_ns = {"pi": "http://pretextbook.org/2020/pretext/internal"}
    manifest = common.xsltproc(extraction_xslt, xml_source, None, dest_dir, stringparams)
    for entry in manifest.getroot().findall("pi:qrcode", pi_ns):
        the_id = entry.get("id")
        url_file = os.path.join(dest_dir, the_id + "-url.xml")
        tree = ET.parse(url_file)
        url = tree.find("pi:standalone-url", pi_ns).text
        path = os.path.join(dest_dir, the_id + ".png")
        log.info('creating URL with content "{}" as {}...'.format(url, path))
        if has_image:
            error_correction = qrcode.constants.ERROR_CORRECT_H
        else:
            error_correction = qrcode.constants.ERROR_CORRECT_L
        qr = qrcode.QRCode(version=None, error_correction=error_correction, box_size=10, border=0)
        qr.add_data(url)
        if has_image:
            qr_image = qr.make_image(
                image_factory=qrcode.image.styledpil.StyledPilImage, embedded_image_path=image_path
            )
        else:
            qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_image.save(path)
    log.info("QR code creation complete")


#
#


def mermaid_images(xml_source, pub_file, stringparams, xmlid_root, dest_dir, outformat):

    import glob
    import json

    msg = "converting Mermaid diagrams from {} to {} graphics for placement in {}"
    log.info(msg.format(xml_source, outformat, dest_dir))

    mmd_executable_cmd = common.get_executable_cmd("mermaid")
    log.debug("Mermaid executable command: {}".format(mmd_executable_cmd))

    tmp_dir = common.get_temporary_directory()
    log.debug("temporary directory: {}".format(tmp_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-mermaid.xsl")

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root

    log.info("extracting Mermaid diagrams from {}".format(xml_source))
    log.info("string parameters passed to extraction stylesheet: {}".format(stringparams))
    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)

    pub_vars = common.get_publisher_variable_report(xml_source, pub_file, stringparams)
    mermaid_theme = common.get_publisher_variable(pub_vars, "mermaid-theme")
    mermaid_layout_engine = common.get_publisher_variable(pub_vars, "mermaid-layout-engine")

    with common.working_directory(tmp_dir):
        mmd_config = {"theme": mermaid_theme, "layout": mermaid_layout_engine}
        mmd_config_file = os.path.join(tmp_dir, "mermaid-config.json")
        with open(mmd_config_file, "w", encoding="utf-8") as config_file:
            json.dump(mmd_config, config_file, indent=4)
        log.debug("Mermaid configuration file: {}".format(mmd_config_file))
        if outformat not in ["png", "svg"]:
            log.error("cannot make Mermaid diagrams in {} file format".format(outformat))
            return
        for mmddiagram in glob.glob(os.path.join(tmp_dir, "*.mmd")):
            filebase, _ = os.path.splitext(mmddiagram)
            mmdout = "{}.{}".format(filebase, outformat)
            mmd_cmd = mmd_executable_cmd + ["-i", mmddiagram, "-o", mmdout, "-s", "4", "-c", "mermaid-config.json"]
            log.debug("mermaid conversion command: {}".format(" ".join(mmd_cmd)))
            subprocess.call(mmd_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            if os.path.exists(mmdout):
                shutil.copy2(mmdout, dest_dir)
            else:
                msg = "the Mermaid output {} was not built"
                log.warning(msg.format(mmdout))


#
#


#
#


def preview_images(xml_source, pub_file, stringparams, xmlid_root, dest_dir, method):
    import asyncio

    try:
        import playwright.async_api
    except ImportError:
        raise ImportError(__module_warning.format("playwright"))

    async def generate_previews(interactives, baseurl, dest_dir, timeout, design_width):

        async with playwright.async_api.async_playwright() as pw:
            browser = await pw.chromium.launch()
            viewport_height = 1000
            page = await browser.new_page(viewport={"width": design_width, "height": viewport_height})
            calibrated = False
            fail_ms = 5000
            failures = []
            for preview_fragment in interactives:
                input_page = baseurl + "/" + preview_fragment + ".html"
                filename = preview_fragment + "-preview.png"

                xpath = "//iframe[@id='{}'][1]".format(preview_fragment)

                msg = 'automatic screenshot of interactive with identifier "{}" on page {} to file {}'
                log.info(msg.format(preview_fragment, input_page, filename))

                try:
                    await page.goto(input_page, wait_until="domcontentloaded", timeout=fail_ms)
                    if not calibrated:
                        measure = "id => document.getElementById(id).parentElement.getBoundingClientRect().width"
                        available = await page.evaluate(measure, preview_fragment)
                        shortfall = round(design_width - available)
                        if shortfall > 0:
                            await page.set_viewport_size({"width": design_width + shortfall, "height": viewport_height})
                            await page.goto(input_page, wait_until="domcontentloaded", timeout=fail_ms)
                        calibrated = True
                    await page.wait_for_timeout(timeout)
                    elt = page.locator(xpath)
                    await elt.screenshot(path=filename, scale="css", timeout=fail_ms)
                    shutil.copy2(filename, dest_dir)
                except Exception as e:
                    failures.append(preview_fragment)
                    msg = 'could not capture a preview image for the interactive with identifier "{}" ({}); a static substitute will be used'
                    log.error(msg.format(preview_fragment, type(e).__name__))
            if failures:
                msg = "{} of {} interactive preview images captured; none produced for: {}"
                log.error(msg.format(len(interactives) - len(failures), len(interactives), ", ".join(failures)))
            await browser.close()

    def start_server():
        try:
            import http.server
            import socketserver
            import threading
            import random
        except ImportError:
            raise ImportError("http.server, socketserver, threading, random")

        class MyHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                log.debug("http.server: " + format % args)
                return

        port = 8888
        attempts = 0
        max_attempts = 10
        while attempts < max_attempts:
            try:
                log.debug("Trying http.server on port {}".format(port))
                server = socketserver.TCPServer(("localhost", port), MyHandler)
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                log.debug(f"Started http.server on port {port}")
                return port, server
            except Exception as e:
                log.debug("http.server error: port {} in use; (error {})".format(port, e))
                port = random.randint(49152, 65535)
                attempts += 1
        else:
            raise OSError("Unable to open http.server for interactive previews")

    def stop_server(server):
        try:
            log.debug("Stopping http.server")
            server.shutdown()
            log.debug("http.server shutdown successful")
        except Exception as e:
            log.warning("http.server shutdown failed; perhaps it wasn't running? error: {}".format(e))

    log.info(
        "using playwright package to create previews for interactives from {} for placement in {}".format(
            xml_source, dest_dir
        )
    )

    timeout = 10000 if method == "slow" else 5000

    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-interactive.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    tmp_dir = common.get_temporary_directory()
    id_filename = os.path.join(tmp_dir, "interactives-ids.txt")
    log.debug("Interactives id list temporarily in {}".format(id_filename))
    log.debug("Interactives html files temporarily in {}".format(tmp_dir))
    common.xsltproc(extraction_xslt, xml_source, id_filename, tmp_dir, stringparams)
    with open(id_filename, "r", encoding="utf-8") as id_file:
        interactives = [f.strip() for f in id_file.readlines() if not f.isspace()]

    pub_vars = common.get_publisher_variable_report(xml_source, pub_file, stringparams)
    design_width = int(common.get_publisher_variable(pub_vars, "html-design-width"))

    _, external_abs = common.get_managed_directories(xml_source, pub_file)
    common.copy_managed_directories(tmp_dir, external_abs=external_abs)
    copy_html_js(tmp_dir)

    with common.working_directory(tmp_dir):
        try:
            log.debug("Starting event loop for playwright, after starting server")
            port, server = start_server()
            baseurl = "http://localhost:{}".format(port)
            asyncio.run(generate_previews(interactives, baseurl, dest_dir, timeout, design_width))
        finally:
            log.info("Closing http.server thread")
            if server:
                stop_server(server)


def all_images(xml, pub_file, stringparams, xmlid_root):

    src_tree = ET.parse(xml)
    src_tree.xinclude()

    has_gdscript = bool(src_tree.xpath("/pretext/*[not(docinfo)]//program[@pck and @interactive='activecode']"))
    has_latex_image = bool(src_tree.xpath("/pretext/*[not(docinfo)]//latex-image"))
    has_asymptote = bool(src_tree.xpath("/pretext/*[not(docinfo)]//asymptote"))
    has_sageplot = bool(src_tree.xpath("/pretext/*[not(docinfo)]//sageplot"))
    has_youtube = bool(src_tree.xpath("/pretext/*[not(docinfo)]//video[@youtube]"))
    has_preview = bool(src_tree.xpath("/pretext/*[not(docinfo)]//interactive[not(@preview)]"))

    # has_latex_image = False
    # has_asymptote = False
    # has_sageplot = False
    # has_youtube = False
    # has_preview = False

    if not (pub_file):
        msg = " ".join([
            "creating all images requires a directory specification",
            "in a publisher file, and no publisher file has been given",
        ])
        raise ValueError(msg)
    generated_dir, _ = common.get_managed_directories(xml, pub_file)

    if not (generated_dir):
        msg = " ".join([
            "creating all images requires a directory specified in the",
            "publisher file in the attribute /publication/source/directories/@generated",
        ])
        raise ValueError(msg)

    #
    if has_latex_image:
        dest_dir = os.path.join(generated_dir, "latex-image", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        latex_image_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "pdf", True, None)
        latex_image_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "svg", True, None)

    #
    if has_asymptote:
        dest_dir = os.path.join(generated_dir, "asymptote", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        asymptote_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "pdf", None)
        asymptote_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "html", None)

    #
    if has_sageplot:
        dest_dir = os.path.join(generated_dir, "sageplot", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        sage_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "pdf", None)
        sage_conversion(xml, pub_file, stringparams, xmlid_root, dest_dir, "svg", None)

    #
    if has_gdscript:
        dest_dir = os.path.join(generated_dir, "gdscript", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        gdscript_pck(xml, pub_file, stringparams, xmlid_root, dest_dir)

    #
    if has_youtube:
        dest_dir = os.path.join(generated_dir, "youtube", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        youtube_thumbnail(xml, pub_file, stringparams, xmlid_root, dest_dir)

    #
    if has_preview:
        dest_dir = os.path.join(generated_dir, "preview", "")
        if not (os.path.isdir(dest_dir)):
            os.mkdir(dest_dir)
        preview_images(xml, pub_file, stringparams, xmlid_root, dest_dir)


#
#


def mom_static_problems(xml_source, pub_file, stringparams, xmlid_root, dest_dir):

    import urllib.parse
    import PIL.Image
    import shutil
    import asyncio

    stringparams = stringparams.copy()

    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))
    try:
        import playwright.async_api
    except ImportError:
        raise ImportError(__module_warning.format("playwright"))

    log.info("downloading MyOpenMath static problems from {} for placement in {}".format(xml_source, dest_dir))
    ptx_xsl_dir = common.get_ptx_xsl_path()
    extraction_xslt = os.path.join(ptx_xsl_dir, "extract-mom.xsl")
    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    tmp_dir = common.get_temporary_directory()
    id_filename = os.path.join(tmp_dir, "mom-ids.txt")
    log.debug("MyOpenMath id list temporarily in {}".format(id_filename))
    common.xsltproc(extraction_xslt, xml_source, id_filename, None, stringparams)
    images_dir = os.path.join(dest_dir, "images")
    if not (os.path.isdir(images_dir)):
        os.mkdir(images_dir)
    with open(id_filename, "r", encoding="utf-8") as id_file:
        problems = [p.strip() for p in id_file.readlines() if not p.isspace()]

    for problem in problems:
        url = f"https://www.myopenmath.com/util/mbx.php?id={problem}&preservesvg=true"
        path = os.path.join(dest_dir, f"mom-{problem}.xml")
        log.info(f"downloading MOM #{problem} to {path}...")

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()

            xml_content = f'<?xml version="1.0" encoding="utf-8"?>\n{r.text}'
            xml_content = xml_content.replace(
                "<myopenmath", '<myopenmath xmlns:pi="http://pretextbook.org/2020/pretext/internal"'
            )
            tree = ET.fromstring(xml_content.encode("utf-8"))

            image_elements = tree.xpath("//image[contains(@source, 'http')]")
            count = 1
            for image_element in image_elements:
                image_url = image_element.get("source")
                image_url_parsed = urllib.parse.urlparse(image_url)
                source_filename = os.path.basename(image_url_parsed.path)
                _, source_ext = os.path.splitext(source_filename)
                if source_ext:
                    image_filename = f"mom-{problem}-{count}{source_ext}"
                else:
                    image_filename = f"mom-{problem}-{count}"
                    log.info(f"No file name extension for MOM {problem} image {count}; results are unpredictable.")
                imageloc = f"problems/images/{image_filename}"
                image_path = os.path.join(images_dir, image_filename)

                try:
                    imageresp = requests.get(image_url, stream=True, timeout=10)
                    imageresp.raise_for_status()
                    with open(image_path, "wb") as imagefile:
                        imageresp.raw.decode_content = True
                        shutil.copyfileobj(imageresp.raw, imagefile)
                    try:
                        img = PIL.Image.open(image_path)
                        imgwidthtag = min(100, round(img.width / 6))
                        img.close()
                        image_element.set("width", "{}%".format(imgwidthtag))
                    except Exception as e:
                        log.error("Unable to read image width of {}: {}".format(image_path, e))

                    del image_element.attrib["source"]
                    image_element.set("{http://pretextbook.org/2020/pretext/internal}generated", imageloc)
                except requests.exceptions.RequestException as e:
                    log.error(f"Error downloading image {image_url}: {e}")
                count += 1

            image_svg_elements = tree.xpath("//image/*[local-name()='svg']")
            for svg_element in image_svg_elements:
                if svg_element is not None:
                    svg_string = f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n{ET.tostring(svg_element, encoding="unicode")}'
                    svg_string = svg_string.replace(' xmlns:pi="http://pretextbook.org/2020/pretext/internal"', "")
                    svgname = f"images/mom-{problem}-{count}"
                    svgname_ext = f"{svgname}.svg"
                    svgpath = os.path.join(dest_dir, svgname_ext)
                    pdfname_ext = f"{svgname}.pdf"
                    pdfpath = os.path.join(dest_dir, pdfname_ext)
                    pngname_ext = f"{svgname}.png"
                    pngpath = os.path.join(dest_dir, pngname_ext)

                    with open(svgpath, "w", encoding="utf-8") as svgfile:
                        svgfile.write(svg_string)
                        svgfile.close()

                    svg_width = svg_element.get("width")
                    svg_height = svg_element.get("height")
                    svg_viewbox = svg_element.get("viewBox")
                    svg_width_parsed = re.search(r"([0-9\.]+)([a-zA-Z%]*)", svg_width)
                    svg_height_parsed = re.search(r"([0-9\.]+)([a-zA-Z%]*)", svg_height)
                    if svg_width:
                        svg_units = svg_width_parsed.group(2).lower()

                    width = svg_width
                    height = svg_height
                    if svg_units == "%":
                        height = None
                        width = None
                    elif svg_units == "pt":
                        height = str(float(svg_height_parsed.group(1)) / 72 * 96) + "px"
                        width = str(float(svg_width_parsed.group(1)) / 72 * 96) + "px"

                    if (not height or not width) and svg_viewBox:
                        viewBox_values = svg_viewbox.split(" ")
                        height = str(float(viewBox_values[3]) - float(viewBox_values[1])) + "px"
                        width = str(float(viewBox_values[2]) - float(viewBox_values[0])) + "px"

                    async def write_pdf(svg_string):
                        static_html = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="utf-8" />
                            <meta name="viewport" content="width=device-width,initial-scale=1" />
                            <style>
                            /* prevent page breaks after svg */
                            * {{
                                margin:0;
                                padding:0;
                                white-space:nowrap;
                                overflow: hidden;
                                line-height: 0;
                            }}
                            </style>
                            </head>
                        <body>
                        {svg_string}
                        </body>
                        </html>"""

                        async with playwright.async_api.async_playwright() as pw:
                            browser = await pw.chromium.launch()
                            page = await browser.new_page()
                            await page.set_content(static_html)
                            await page.pdf(path=pdfpath, width=width, height=height)
                            await page.locator("svg").screenshot(path=pngpath, scale="device")

                            await browser.close()

                    asyncio.run(write_pdf(svg_string))

                    if svg_width_parsed:
                        if svg_units:
                            if svg_units == "mm":
                                svg_scale = 158.8
                            elif svg_units == "cm":
                                svg_scale = 15.88
                            elif svg_units == "in":
                                svg_scale = 6.25
                            else:
                                svg_scale = 600
                            imgwidthtag = min(100, round(100 * float(svg_width_parsed.group(1)) / svg_scale))
                        else:
                            imgwidthtag = 100
                    else:
                        imgwidthtag = 100
                    svg_element.getparent().set("width", f"{imgwidthtag}%")
                    svg_element.getparent().set(
                        "{http://pretextbook.org/2020/pretext/internal}generated", f"problems/{svgname}"
                    )
                    svg_element.getparent().remove(svg_element)

                    count += 1

            with open(path, "wb") as f:
                f.write(ET.tostring(tree, encoding="utf-8", xml_declaration=True))

        except requests.exceptions.RequestException as e:
            log.error(f"Error downloading MOM #{problem}: {e}")
        except ET.XMLSyntaxError as e:
            log.error(f"Error parsing XML for MOM #{problem}: {e}")
        except Exception as e:
            log.error(f"An unexpected error occurred for MOM #{problem}: {e}")

    log.info("MyOpenMath static problem download complete")


def text(xml, pub_file, stringparams, out_file, dest_dir, text_format):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file

    text_format_stylesheets = {
        "text": "pretext-text.xsl",
        "markdown": "pretext-markdown.xsl",
        "markdown-zip": "pretext-markdown.xsl",
    }
    text_format_extensions = {
        "text": ".txt",
        "markdown": ".md",
        "markdown-zip": ".md",
    }

    msg = "converting {} to {} format in {}"
    log.info(msg.format(xml, text_format, dest_dir))

    conversion_xslt = os.path.join(common.get_ptx_xsl_path(), text_format_stylesheets[text_format])
    b_zip = text_format == "markdown-zip"
    if b_zip:
        basename = os.path.splitext(os.path.basename(xml))[0]
        staging_parent = common.get_temporary_directory()
        work_dir = os.path.join(staging_parent, basename)
        os.mkdir(work_dir)
    else:
        work_dir = dest_dir
    result_tree = common.xsltproc(conversion_xslt, xml, None, work_dir, stringparams)
    if str(result_tree):
        derivedname = common.get_output_filename(
            xml, None if b_zip else out_file, work_dir, text_format_extensions[text_format]
        )
        result_tree.write_output(derivedname)
        log.info("{} file deposited as {}".format(text_format, derivedname))
    else:
        log.info("{} files deposited in {}".format(text_format, work_dir))
    if text_format in ("markdown", "markdown-zip"):
        generated_abs, external_abs = common.get_managed_directories(xml, pub_file)
        if external_abs:
            shutil.copytree(external_abs, os.path.join(work_dir, "external"), dirs_exist_ok=True)
        if generated_abs:
            shutil.copytree(generated_abs, os.path.join(work_dir, "generated"), dirs_exist_ok=True)
    if b_zip:
        zip_filename = shutil.make_archive(os.path.join(dest_dir, basename), "zip", staging_parent, basename)
        log.info("markdown bundle deposited as {}".format(zip_filename))


def braille(xml_source, pub_file, stringparams, out_file, dest_dir, page_format):

    stringparams = stringparams.copy()

    log.info("converting {} into BRF in {} combining UEB2 and Nemeth".format(xml_source, dest_dir))

    chunk_level = ""
    if pub_file:
        pub_tree = ET.parse(pub_file)
        pub_tree.xinclude()
        chunk_elt = pub_tree.xpath("/publication/common/chunking")
        if chunk_elt:
            attrs = chunk_elt[0].attrib
            if "level" in attrs:
                chunk_level = chunk_elt[0].attrib["level"]
                if chunk_level in ["0", "1"]:
                    msg = 'braille chunking level (from publisher file) set to "{}"'
                    log.info(msg.format(chunk_level))
                else:
                    msg = 'braille chunking level in publisher file should be "0" or "1", not "{}".'
                    log.warning(msg.format(chunk_level))
                    chunk_level = ""
    if chunk_level == "":
        msg = 'braille chunking level was never elected properly in a publisher file, using default value, "0".'
        log.debug(msg)
        chunk_level = "0"

    log.warning("Any elective chunking is temporarily disabled")
    chunk_level = "0"

    tmp_dir = common.get_temporary_directory()
    log.debug("Braille manufacture in temporary directory: {}".format(tmp_dir))

    math_format = "nemeth"
    math_representations = os.path.join(tmp_dir, "math-representations-{}.xml".format(math_format))

    msg = "converting raw LaTeX from {} into clean {} format placed into {}"
    log.debug(msg.format(xml_source, math_format, math_representations))
    mathjax_latex(xml_source, pub_file, math_representations, None, math_format, False)

    msg = "converting source ({}) and clean representations ({}) into preprint XML file ({})"
    stringparams["mathfile"] = math_representations.replace(os.sep, "/")
    stringparams["page-format"] = page_format
    if pub_file:
        stringparams["publisher"] = pub_file
    preprint = os.path.join(tmp_dir, "preprint.xml")
    braille_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-braille-preprint.xsl")
    common.xsltproc(braille_xslt, xml_source, preprint, tmp_dir, stringparams)

    from . import braille_translate
    from . import braille_format

    translated = os.path.join(tmp_dir, "translated.xml")
    msg = "translating print text of preprint ({}) into braille ({})"
    log.debug(msg.format(preprint, translated))
    braille_translate.translate_document(preprint, translated)

    temp_brf = os.path.join(tmp_dir, "temporary.brf")
    braille_format.parse_segments(translated, temp_brf, page_format)

    if chunk_level == "0":
        final_brf = common.get_output_filename(xml_source, out_file, dest_dir, ".brf")
        shutil.copyfile(temp_brf, final_brf)
        log.info("Single BRF file deposited as {}".format(final_brf))
    if chunk_level == "1":
        with common.working_directory(dest_dir):
            _split_brf(temp_brf)
            log.info("BRF file chunked and deposited in {}".format(dest_dir))


def _split_brf(filename):

    #
    #

    brf_numbers = "abcdefghij"
    num_numbers = "1234567890"
    brf_to_num_dict = dict(zip(brf_numbers, num_numbers))
    num_to_brf_dict = dict(zip(num_numbers, brf_numbers))

    def brf_to_num(string):
        out = ""
        for char in string:
            out += brf_to_num_dict[char]
        return int(out)

    def num_to_brf(num):
        out = ""
        for char in str(num):
            out += num_to_brf_dict[char]
        return out

    class Chapter:
        def __init__(self, start_page_num, numbered_chapter, chapter_number):
            self.start_page = start_page_num
            self.numbered = numbered_chapter
            self.number = chapter_number
            self.end_page = -1
            self.body = []
            self.front_matter = True

        def get_body(self, pages):
            for page_num in range(self.start_page, self.end_page):
                self.body += pages[page_num]

        def write_body(self):
            if self.numbered:
                out_filename = f"chapter_{self.number:02d}.brf"
            elif self.front_matter:
                out_filename = f"frontmatter_{self.number}.brf"
            else:
                out_filename = f"backmatter_{self.number}.brf"

            with open(out_filename, "w", encoding="utf-8") as g:
                g.writelines(self.body)

    def is_chapter_name(line):
        if len(re.findall("^[ ]{2}[,|#]", line)) > 0:
            chapter_name = True
            if len(re.findall("^[ ]{2}#([a-j]+?) ", line)) > 0:
                numbered_chapter = True
                chapter_number = brf_to_num(re.findall("^[ ]{2}#([a-j]+?) ", line)[0])
            elif len(re.findall("^[ ]{2},\\*apt} #([a-j]+?) ", line)) > 0:
                numbered_chapter = True
                chapter_number = brf_to_num(re.findall("^[ ]{2},\\*apt} #([a-j]+?) ", line)[0])
            else:
                numbered_chapter = False
                chapter_number = -1
        else:
            chapter_name = False
            numbered_chapter = False
            chapter_number = -1
        return (chapter_name, numbered_chapter, chapter_number)

    #
    #
    #
    #
    #
    #
    #

    def find_chapter_page_num(line):
        if len(re.findall(" [']{2,35} #", line)) > 0:
            m = re.search("[']{2,35} #(.+?)[ |\n]", line)

            return (True, brf_to_num(m.group(1)))
        elif len(line) < 40:
            return (False, -1)
        elif len(re.findall(" #([a-j]+?)  #[a-j]+?$", line)) > 0:
            page = brf_to_num(re.findall(" #([a-j]+?)  #[a-j]+?$", line)[0])
            return (True, page)
        elif len(re.findall("[ ]{4,35}#[a-j]+?$", line)) > 0:
            return (False, -1)
        elif len(re.findall("[ ]{1,3}#([a-j]+?)$", line)) > 0:
            page = brf_to_num(re.findall("[ ]{1,3}#([a-j]+?)$", line)[0])
            return (True, page)
        else:
            raise ValueError(f"A weird long TOC line found:\n{line}")

    #
    #

    def get_TOC(filename):
        f = open(filename, "r", encoding="latin-1")
        front_matter = []
        TOC = []
        text_body = []

        is_contents = False

        while not is_contents:
            line = f.readline()
            front_matter.append(line)
            if line == "":
                raise ValueError("Reached the end of file while looking for Table of Contents")

            if len(re.findall("3t5ts", line)) > 0:
                if re.search("3t5ts", line).start() > 10 and re.search("3t5ts", line).end() < 30:
                    is_contents = True
                    log.debug("TOC found")

        while is_contents:
            line = f.readline()

            if line == "":
                raise ValueError("Reached end of file while reading the Table of Contents")

            trailing_spaces = 40 - len(line) - 2
            pattern = f"\f[ ]{ {trailing_spaces} }"
            if len(re.findall(pattern, line)) == 0:
                TOC.append(line)
                front_matter.append(line)
            else:
                temp_line = line
                line = f.readline()

                if line == "\n":
                    is_contents = False
                    log.debug(f"Found the end of TOC:\n{temp_line}")
                    text_body.append(temp_line)
                    text_body.append(line)
                else:
                    TOC.append(temp_line)
                    TOC.append(line)
                    front_matter.append(temp_line)
                    front_matter.append(line)

        while line != "":
            line = f.readline()
            text_body.append(line)

        f.close()
        return (TOC, front_matter, text_body)

    def get_chapter_list(TOC):
        chapter_list = []
        line_number = 0

        while line_number < len(TOC) - 1:
            line = TOC[line_number]
            (chapter_name, numbered_chapter, chapter_number) = is_chapter_name(line)
            if chapter_name:
                (page_num_found, start_page_num) = find_chapter_page_num(line)
                while not page_num_found:
                    line_number += 1
                    if line_number == len(TOC) - 1:
                        raise ValueError("Reached end of TOC while looking for the page number")

                    line = TOC[line_number]
                    (page_num_found, start_page_num) = find_chapter_page_num(line)

                chapter_list.append(Chapter(start_page_num, numbered_chapter, chapter_number))

            line_number += 1
        return chapter_list

    def split_body_into_pages(text_body):
        pages = dict()

        if len(re.findall("\f", text_body[0])) == 0:
            raise ValueError("Unexpected first line of body text: does not start with new page character")
        current_page = [text_body[0]]

        for number, line in enumerate(text_body[1:]):
            if line != "":
                if len(re.findall("\f", line)) == 0:
                    current_page.append(line)
                else:
                    prev_line = text_body[number]

                    if len(re.findall("[ ]{2}#([a-j]+?)$", prev_line)) == 0:
                        raise ValueError(f"Page number not found, expected to be on the line\n{prev_line}")
                    else:
                        page_num = brf_to_num(re.findall("[ ]{2}#([a-j]+?)$", prev_line)[0])
                        pages[page_num] = current_page
                        current_page = [line]
        log.debug(f"Successfully split text into {page_num} pages")
        return pages

    def write_chapters(chapter_list, front_matter, text_body, split_frontmatter=False, split_backmatter=False):

        pages = split_body_into_pages(text_body)
        is_front_matter = True
        unnumbered_counter = 1
        back_matter = []

        for index in range(len(chapter_list)):
            chapter = chapter_list[index]
            if index < len(chapter_list) - 1:
                chapter.end_page = chapter_list[index + 1].start_page
            else:
                chapter.end_page = max([num for num in pages.keys()]) + 1
            chapter.get_body(pages)

            if chapter.numbered:
                is_front_matter = False
                unnumbered_counter = 1

                chapter.write_body()

            elif is_front_matter:
                chapter.front_matter = True
                if split_frontmatter:
                    chapter.number = unnumbered_counter
                    chapter.write_body()
                    unnumbered_counter += 1
                else:
                    front_matter += chapter.body

            else:
                chapter.front_matter = False
                if split_backmatter:
                    chapter.number = unnumbered_counter
                    chapter.write_body()
                    unnumbered_counter += 1
                else:
                    back_matter += chapter.body

            with open("frontmatter.brf", "w", encoding="utf-8") as g:
                g.writelines(front_matter)
            if back_matter != []:
                with open("backmatter.brf", "w", encoding="utf-8") as g:
                    g.writelines(back_matter)

    toc, frontmatter, bodytext = get_TOC(filename)
    chapters = get_chapter_list(toc)
    write_chapters(chapters, frontmatter, bodytext)


def _sanitize_svg_for_epub(directory):
    import glob

    parser = ET.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    for svg_file in glob.glob(os.path.join(directory, "**", "*.svg"), recursive=True):
        try:
            tree = ET.parse(svg_file, parser=parser)
        except Exception:
            log.warning(
                "could not parse {} to sanitize it for EPUB; it will be employed unchanged and may cause validation errors".format(
                    svg_file
                )
            )
            continue
        root = tree.getroot()
        svg_namespace = "http://www.w3.org/2000/svg"
        xlink_namespace = "http://www.w3.org/1999/xlink"
        referenced = set()
        for element in root.iter():
            for key in ["{{{}}}href".format(xlink_namespace), "href"]:
                value = element.get(key)
                if value and value.startswith("#"):
                    referenced.add(value[1:])
        for path in root.iter("{{{}}}path".format(svg_namespace)):
            if not path.get("d"):
                if path.get("id") in referenced:
                    path.set("d", "M0 0")
                else:
                    parent = path.getparent()
                    if parent is not None:
                        parent.remove(path)
        for element in root.iter("{{{}}}*".format(svg_namespace)):
            if element.get("name") is not None:
                del element.attrib["name"]
        if root.get("role") and root.get("role") not in ["application", "document", "img"]:
            root.set("role", "img")
        with open(svg_file, "wb") as handle:
            handle.write(ET.tostring(root, xml_declaration=True, encoding="utf-8"))


def epub(xml_source, pub_file, out_file, dest_dir, file_format, math_format, stringparams):

    stringparams = stringparams.copy()

    import fileinput

    import PIL.Image
    import PIL.ImageDraw
    import PIL.ImageFont

    log.info("converting {} into EPUB in {} with math as {}".format(xml_source, dest_dir, math_format))

    tmp_dir = common.get_temporary_directory()
    log.debug("EPUB manufacture in temporary directory: {}".format(tmp_dir))

    source_dir = common.get_source_path(xml_source)
    epub_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-epub.xsl")
    math_representations = os.path.join(tmp_dir, "math-representations-{}.xml".format(math_format))
    speech_representations = os.path.join(tmp_dir, "math-representations-{}.xml".format("speech"))
    packaging_file = os.path.join(tmp_dir, "packaging.xml")
    xhtml_dir = os.path.join(tmp_dir, "EPUB", "xhtml")

    msg = "converting raw LaTeX from {} into clean {} format placed into {}"
    log.debug(msg.format(xml_source, math_format, math_representations))
    mathjax_latex(xml_source, pub_file, math_representations, None, math_format, False)
    if math_format == "svg":
        log.debug(msg.format(xml_source, "speech", speech_representations))
        mathjax_latex(xml_source, pub_file, speech_representations, None, "speech", False)

    log.info(
        "converting source ({}) and clean representations ({}) into EPUB files".format(xml_source, math_representations)
    )
    params = {}

    params["mathfile"] = math_representations.replace(os.sep, "/")
    if math_format == "svg":
        params["speechfile"] = speech_representations.replace(os.sep, "/")
    else:
        params["speechfile"] = ""
    params["math.format"] = math_format
    params["tmpdir"] = tmp_dir.replace(os.sep, "/")
    if pub_file:
        params["publisher"] = pub_file
    common.xsltproc(epub_xslt, xml_source, packaging_file, tmp_dir, {**params, **stringparams})

    orig = "<html"
    repl = __xml_header + '<html xmlns="http://www.w3.org/1999/xhtml"'
    with common.working_directory(xhtml_dir):
        html_elt = re.compile(orig)
        for root, dirs, files in os.walk(xhtml_dir):
            for fn in files:
                with fileinput.FileInput(fn, inplace=True, encoding="utf-8") as file:
                    for line in file:
                        print(html_elt.sub(repl, line), end="")

    packaging_tree = ET.parse(packaging_file)

    css_dir = os.path.join(tmp_dir, "EPUB", "css")
    os.mkdir(css_dir)

    if math_format == "kindle":
        css = os.path.join(common.get_ptx_xsl_path(), "..", "css", "dist", "kindle.css")
        shutil.copy2(css, css_dir)
    else:
        css = os.path.join(common.get_ptx_xsl_path(), "..", "css", "dist", "epub.css")
        shutil.copy2(css, css_dir)

    #

    is_cover_authored = packaging_tree.xpath("/packaging/cover/@authored-cover")[0] == "yes"
    if is_cover_authored:
        cover_source_file = packaging_tree.xpath("/packaging/cover/@source")[0]
        cover_dest_file = packaging_tree.xpath("/packaging/cover/@dest")[0]
        cover_source = os.path.join(source_dir, str(cover_source_file))
        cover_dest = os.path.join(xhtml_dir, str(cover_dest_file))
        os.makedirs(os.path.dirname(cover_dest), exist_ok=True)
        shutil.copy2(cover_source, cover_dest)
    else:
        cover_source = os.path.join(tmp_dir, "cover.png")
        cover_dest = os.path.join(xhtml_dir, "cover.png")
        title = packaging_tree.xpath("/packaging/title")[0].xpath("string()").__str__()
        subtitle = packaging_tree.xpath("/packaging/subtitle")[0].xpath("string()").__str__()
        author = packaging_tree.xpath("/packaging/author")[0].xpath("string()").__str__()
        title_ASCII = "".join([x if ord(x) < 128 else "?" for x in title])
        subtitle_ASCII = "".join([x if ord(x) < 128 else "?" for x in subtitle])
        author_ASCII = "".join([x if ord(x) < 128 else "?" for x in author])
        log.info("attempting to construct cover image using LaTeX and ImageMagick")
        try:
            latex_key = common.get_deprecated_tex_fallback("xelatex")
            tex_executable_cmd = common.get_executable_cmd(latex_key)
            cover_tex_template = "\\documentclass[20pt]{{scrartcl}}\\begin{{document}}\\title{{ {} }}\\subtitle{{ {} }}\\author{{ {} }}\\date{{}}\\maketitle\\thispagestyle{{empty}}\\end{{document}}"
            if "xelatex" in tex_executable_cmd:
                cover_tex = cover_tex_template.format(title, subtitle, author.replace(", ", "\\\\"))
            else:
                cover_tex = cover_tex_template.format(title_ASCII, subtitle_ASCII, author_ASCII)
            cover_tex_file = os.path.join(tmp_dir, "cover.tex")
            with open(cover_tex_file, "w", encoding="utf-8") as tex:
                tex.write(cover_tex)
            latex_cmd = tex_executable_cmd + ["-interaction=batchmode", cover_tex_file]
            cover_pdf_file = os.path.join(tmp_dir, "cover.pdf")
            pdfpng_executable_cmd = ["convert"]
            png_cmd = pdfpng_executable_cmd + [
                "-quiet",
                "-density",
                "300",
                cover_pdf_file + "[0]",
                "-gravity",
                "center",
                "-crop",
                "5:8",
                "-background",
                "white",
                "-alpha",
                "remove",
                "-quality",
                "100",
                cover_source,
            ]
            with common.working_directory(tmp_dir):
                subprocess.run(latex_cmd)
                subprocess.run(png_cmd)
        except:
            msg = "\n".join([
                "failed to construct cover image using LaTeX and ImageMagick",
                'perhaps because the "convert" executable is not on your path.',
            ])
            log.warning(msg)
            log.info('attempting to construct cover image using "Arial.ttf" and "Arial Bold.ttf"')
            try:
                title_size = 100
                title_font = PIL.ImageFont.truetype("Arial Bold.ttf", title_size)
                subtitle_size = int(title_size * 0.6)
                subtitle_font = PIL.ImageFont.truetype("Arial Bold.ttf", subtitle_size)
                author_size = subtitle_size
                author_font = PIL.ImageFont.truetype("Arial.ttf", author_size)
                title_words = title.split()
                subtitle_words = subtitle.split()
                author_names = [x.strip() for x in author.split(",")]
                png_width = 1280
                png_height = int(png_width * 1.6)
                title_lines = [""]
                for word in title_words:
                    last_line = title_lines[-1]
                    (line_width, line_height) = title_font.getsize(last_line + " " + word)
                    if line_width <= 0.8 * png_width:
                        title_lines[-1] += " " + word
                    else:
                        title_lines.append(word)
                multiline_title = "\n".join(title_lines).strip()
                subtitle_lines = [""]
                for word in subtitle_words:
                    last_line = subtitle_lines[-1]
                    (line_width, line_height) = subtitle_font.getsize(last_line + " " + word)
                    if line_width <= 0.8 * png_width:
                        subtitle_lines[-1] += " " + word
                    else:
                        subtitle_lines.append(word)
                multiline_subtitle = "\n".join(subtitle_lines).strip()
                multiline_author = "\n".join(author_names).strip()
                cover_png = PIL.Image.new(mode="RGB", size=(png_width, png_height), color="white")
                draw = PIL.ImageDraw.Draw(cover_png)
                title_depth = int(png_height // 4)
                subtitle_depth = title_depth + len(title_lines) * title_size + 0.2 * title_size
                author_depth = subtitle_depth + len(subtitle_lines) * subtitle_size + 0.8 * title_size
                draw.multiline_text(
                    (int(png_width // 2), title_depth),
                    multiline_title,
                    font=title_font,
                    fill="black",
                    anchor="ma",
                    align="center",
                )
                draw.multiline_text(
                    (int(png_width // 2), subtitle_depth),
                    multiline_subtitle,
                    font=subtitle_font,
                    fill="gray",
                    anchor="ma",
                    align="center",
                )
                draw.multiline_text(
                    (int(png_width // 2), author_depth),
                    multiline_author,
                    font=author_font,
                    fill="black",
                    anchor="ma",
                    align="center",
                )
                cover_png.save(cover_source)
            except:
                log.warning('failed to construct cover image using "Arial.ttf" and "Arial Bold.ttf"')
                log.info("attempting to construct crude bitmap font cover image")
                try:
                    title_words = title_ASCII.split()
                    title_font = PIL.ImageFont.load_default()
                    cover_png = PIL.Image.new(mode="RGB", size=(120, 192), color="white")
                    draw = PIL.ImageDraw.Draw(cover_png)
                    y = 20
                    for word in title_words:
                        draw.text((20, y), word, font=title_font, fill="black")
                        y += 10
                    cover_png.save(cover_source)
                except:
                    log.warning("failed to construct a cover image")
        try:
            shutil.copy2(cover_source, cover_dest)
        except:
            log.info("removing references to cover image from package.opf")
            package_opf = os.path.join(tmp_dir, "EPUB/package.opf")
            package_opf_tree = ET.parse(package_opf)
            for meta in package_opf_tree.xpath(
                "//opf:meta[@name='cover']",
                namespaces={"opf": "http://www.idpf.org/2007/opf"},
            ):
                meta.getparent().remove(meta)
            for item in package_opf_tree.xpath(
                "//opf:item[@id='cover-image']",
                namespaces={"opf": "http://www.idpf.org/2007/opf"},
            ):
                item.getparent().remove(item)
            package_opf_tree.write(package_opf)

    images = packaging_tree.xpath("/packaging/images/image[@filename]")
    for im in images:
        sourcename = str(im.get("sourcename"))
        filename = str(im.get("filename"))
        try:
            source = os.path.join(source_dir, sourcename)
            dest = os.path.join(xhtml_dir, filename)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(source, dest)
        except Exception as e:
            msg = 'PTX:BUG: error copying image with sourcename "{}" and filename "{}".  Traceback follows:'
            # traceback.print_exc()
            log.warning(msg.format(sourcename, filename))
            log.warning(traceback.format_exc())

    _sanitize_svg_for_epub(xhtml_dir)

    #
    # os.remove(packaging_file)
    # os.remove(math_representations)

    if file_format == "epub":
        title_file_element = packaging_tree.xpath("/packaging/filename")[0]
        title_file = ET.tostring(title_file_element, method="text").decode("ascii")
        epub_file = "{}-{}.epub".format(title_file, math_format)
        log.info("packaging an EPUB temporarily as {}".format(epub_file))
        with common.working_directory(tmp_dir):
            with zipfile.ZipFile(epub_file, mode="w", compression=zipfile.ZIP_DEFLATED) as epub:
                epub.write("mimetype", compress_type=zipfile.ZIP_STORED)
                for root, dirs, files in os.walk("EPUB"):
                    for name in files:
                        epub.write(os.path.join(root, name))
                for root, dirs, files in os.walk("META-INF"):
                    for name in files:
                        epub.write(os.path.join(root, name))
            derivedname = common.get_output_filename(xml_source, out_file, dest_dir, ".epub")
            log.info("EPUB file deposited as {}".format(derivedname))
            shutil.copy2(epub_file, derivedname)
    elif file_format == "nozip":
        common.copy_build_directory(tmp_dir, dest_dir)
        msg = "EPUB build files produced, but not zipped into a single file; results placed in {}"
        log.info(msg.format(dest_dir))
    else:
        msg = 'PTX:BUG: conversion to EPUB got an unrecognized file format ("{}").  No output results.'
        log.warning(msg.format(file_format))


def jupyter(xml_source, pub_file, stringparams, file_format, out_file, dest_dir):

    stringparams = stringparams.copy()

    try:
        import nbformat
    except ImportError:
        raise ImportError(__module_warning.format("nbformat"))
    import glob

    log.info("converting {} into Jupyter notebooks in {}".format(xml_source, dest_dir))

    tmp_dir = common.get_temporary_directory()
    log.debug("Jupyter notebook manufacture in temporary directory: {}".format(tmp_dir))
    description_dir = common.get_temporary_directory()
    log.info("notebook descriptions are retained in {}".format(description_dir))

    if pub_file:
        stringparams["publisher"] = pub_file
    extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-jupyter.xsl")
    common.xsltproc(extraction_xslt, xml_source, None, tmp_dir, stringparams)

    generated_abs, external_abs = common.get_managed_directories(xml_source, pub_file)
    common.copy_managed_directories(tmp_dir, external_abs=external_abs, generated_abs=generated_abs)

    kernel_display = {"sagemath": "SageMath", "python3": "Python 3"}

    invalid = []
    descriptions = sorted(glob.glob(os.path.join(tmp_dir, "*.ipynb.xml")))
    if not descriptions:
        log.warning("PTX:BUG: the Jupyter conversion produced no notebook descriptions")
    for description in descriptions:
        tree = ET.parse(description)
        root = tree.getroot()
        notebook = nbformat.v4.new_notebook()
        kernel = root.get("kernel")
        notebook.metadata["kernelspec"] = {
            "name": kernel,
            "display_name": kernel_display.get(kernel, kernel),
        }
        for cell in root.iter("cell"):
            source = cell.text if cell.text else ""
            structure = {k: v for k, v in cell.attrib.items() if k != "type"}
            purpose = structure.pop("purpose", None)
            if cell.get("type") == "code":
                new_cell = nbformat.v4.new_code_cell(source)
            else:
                new_cell = nbformat.v4.new_markdown_cell(source)
            if structure:
                new_cell.metadata["pretext"] = structure
            if purpose == "styling":
                new_cell.metadata["jupyter"] = {"source_hidden": True}
                new_cell.metadata["tags"] = ["hide-input"]
                html = source.split("\n", 1)[1] if source.startswith("%%html") else source
                new_cell.outputs.append(nbformat.v4.new_output("display_data", data={"text/html": html}))
            notebook.cells.append(new_cell)
        notebook_file = os.path.splitext(description)[0]
        try:
            nbformat.validate(notebook)
        except Exception:
            invalid.append(os.path.basename(notebook_file))
            log.error(
                'PTX:BUG: notebook "{}" failed validation.  Traceback follows:'.format(os.path.basename(notebook_file))
            )
            log.error(traceback.format_exc())
        nbformat.write(notebook, notebook_file)
        shutil.move(description, description_dir)
    log.info("converted {} notebook descriptions, {} failed validation".format(len(descriptions), len(invalid)))

    if file_format == "collection":
        common.copy_build_directory(tmp_dir, dest_dir)
        log.info("Jupyter notebooks deposited in {}".format(dest_dir))
    elif file_format == "zip":
        with common.working_directory(tmp_dir):
            zip_file = "jupyter-output.zip"
            log.info("packaging a zip file temporarily as {}".format(os.path.join(tmp_dir, zip_file)))
            with zipfile.ZipFile(zip_file, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for root, dirs, files in os.walk("."):
                    for name in files:
                        if name != zip_file:
                            bundle.write(os.path.join(root, name))
            derivedname = common.get_output_filename(xml_source, out_file, dest_dir, ".zip")
            shutil.copy2(zip_file, derivedname)
            log.info("Jupyter notebooks bundled as {}".format(derivedname))
    else:
        msg = 'PTX:BUG: conversion to Jupyter notebooks got an unrecognized file format ("{}").  No output results.'
        log.warning(msg.format(file_format))


def _parse_runestone_services(et):
    #

    rs_js = ""
    for js in et.xpath("/all/js/item"):
        rs_js = rs_js + js.text + ":"
    rs_js = rs_js[:-1]
    rs_css = ""
    for css in et.xpath("/all/css/item"):
        rs_css = rs_css + css.text + ":"
    rs_css = rs_css[:-1]
    rs_cdn_url = et.xpath("/all/cdn-url")[0].text
    rs_version = et.xpath("/all/version")[0].text

    return (rs_js, rs_css, rs_cdn_url, rs_version)


def _set_runestone_stringparams(stringparams, rs_js, rs_css, rs_version):
    stringparams["rs-js"] = rs_js
    stringparams["rs-css"] = rs_css
    stringparams["rs-version"] = rs_version


def _runestone_services(stringparams, ext_rs_methods):

    services_url_template = "https://runestone.academy/cdn/runestone/{}/webpack_static_imports.xml"

    if "debug.rs.version" in stringparams:
        rs_debug_version = stringparams["debug.rs.version"]
        services_url = services_url_template.format(rs_debug_version)
        msg = "\n".join([
            "Requested Runestone Services, version {} from Runestone servers via the  debug.rs.version  string parameter.",
            "This is strictly for DEBUGGING and not for PRODUCTION.  The requested version may not exist,",
            "or there could be a network error and you will get something you did not expect.",
            "Subsequent diagnostic messages may be inaccurate.  Verify your HTML output is as intended.",
        ])
        log.info(msg.format(rs_debug_version))
    elif "debug.rs.dev" in stringparams:
        log.info(
            "Building for local developmental Runestone Services. Make sure to build Runestone Services to _static in the output directory."
        )
    else:
        services_url = services_url_template.format("latest")

    if "debug.rs.dev" in stringparams:
        rs_js, rs_css, rs_cdn_url, rs_version, services_xml = _runestone_debug_service_info()
        _set_runestone_stringparams(stringparams, rs_js, rs_css, rs_version)
        return (rs_js, rs_css, rs_cdn_url, rs_version, services_xml)

    try:
        if ext_rs_methods and "debug.rs.version" not in stringparams:
            services_xml = ext_rs_methods(url=services_url, format="xml")
        else:
            services_xml = query_runestone_services(services_url)
    except Exception as e:
        raise Exception(e)

    services = ET.fromstring(services_xml)
    rs_js, rs_css, rs_cdn_url, rs_version = _parse_runestone_services(services)

    _set_runestone_stringparams(stringparams, rs_js, rs_css, rs_version)
    return (rs_js, rs_css, rs_cdn_url, rs_version, services_xml)


def _runestone_debug_service_info():
    rs_js = "prefix-runtime.bundle.js:prefix-runtime-libs.bundle.js:prefix-runestone.bundle.js"
    rs_css = "prefix-runtime-libs.css:prefix-runestone.css"
    rs_cdn_url = None
    rs_version = "dev"
    services_xml = None
    return (rs_js, rs_css, rs_cdn_url, rs_version, services_xml)


def _cdn_runestone_services(stringparams, ext_rs_methods):

    services_url_template = "https://cdn.jsdelivr.net/gh/pretextbook/html-static@{}/dist/_static/runestone_services.xml"

    if "debug.rs.version" in stringparams:
        log.warning("Building portable html so ignoring the debug.rs.version string param")
        stringparams.pop("debug.rs.version")
    if "debug.rs.dev" in stringparams:
        log.warning("Building portable html so ignoring the debug.rs.dev string param")
        stringparams.pop("debug.rs.dev")

    rs_version = stringparams.get("cli.version") or "latest"
    log.info("Using rs services version {} from the PreTeXt CDN".format(rs_version))
    services_url = services_url_template.format(rs_version)

    try:
        if ext_rs_methods:
            services_xml = ext_rs_methods(url=services_url, format="xml")
        else:
            services_xml = query_runestone_services(services_url)
    except Exception as e:
        raise Exception(e)

    services = ET.fromstring(services_xml)
    rs_js, rs_css, rs_cdn_url, rs_version = _parse_runestone_services(services)

    stringparams["rs-js"] = rs_js
    stringparams["rs-css"] = rs_css
    stringparams["rs-version"] = rs_version
    return None


def query_runestone_services(services_url):

    online_success = True

    try:
        import requests
    except ImportError:
        msg = 'the "requests" module is not available and is necessary for querying the Runestone CDN'
        log.debug(msg)
        online_success = False

    if online_success:
        try:
            services_response = requests.get(services_url, timeout=(1, 10))
        except requests.exceptions.RequestException as e:
            msg = "\n".join([
                'there was a network problem while trying to retrieve "{}"',
                "from the Runestone CDN and the reported problem is:",
                "{}",
            ])
            log.debug(msg.format(services_url, e))
            online_success = False

    if online_success:
        response_status_code = services_response.status_code
        if response_status_code != 200:
            msg = "\n".join(["the file {} was not found at the Runestone CDN", "the server returned response code {}"])
            log.debug(msg.format(services_url, response_status_code))
            online_success = False

    if not (online_success):
        msg = "\n".join([
            "unable to get Runestone Services from the Runestone CDN.",
            "This is due to an error reported immediately prior in the log.",
            "Unable to proceed and build useful HTML output without this.",
        ])
        log.debug(msg)
        raise Exception(msg)
    return services_response.text


def _place_runestone_services(tmp_dir, stringparams, ext_rs_methods):

    rs_js, rs_css, rs_cdn_url, rs_version, services_xml = _runestone_services(stringparams, ext_rs_methods)
    if "debug.rs.dev" not in stringparams:
        msg = "Runestone Services via online CDN query: version {}"
        log.info(msg.format(rs_version))

        build_dir = os.path.join(tmp_dir, "_static")
        services_file_name = "dist-{}.tgz".format(rs_version)
        services_build_path = os.path.join(build_dir, services_file_name)
        services_record_build_path = os.path.join(build_dir, "_runestone-services.xml")
        try:
            msg = "Downloading Runestone Services, version {}"
            log.info(msg.format(rs_version))
            if ext_rs_methods:
                ext_rs_methods(url=rs_cdn_url + services_file_name, out_path=services_build_path, format="tgz")
            else:
                common.download_file(rs_cdn_url + services_file_name, services_build_path)
            log.info("Extracting Runestone Services from archive file")
            import tarfile

            services_file = tarfile.open(services_build_path)
            services_file.extractall(build_dir)
            services_file.close()
            os.remove(services_build_path)
            services_record = open(services_record_build_path, "w", encoding="utf-8")
            services_record.write(services_xml)
            services_record.close()
        except Exception as e:
            log.warning(e)
            log.warning("Failed to download all Runestone Services files")


def _move_prebuilt_theme(theme_name, theme_opts, tmp_dir):
    css_src = os.path.join(common.get_ptx_path(), "css", "dist")
    css_dest = os.path.join(tmp_dir, "_static", "pretext", "css")

    src = os.path.join(common.get_ptx_path(), "css", "dist", "theme-{}.css".format(theme_name))
    dest = os.path.join(common.get_ptx_path(), os.path.join(css_dest, "theme.css"))

    color_schemes = {
        "blue-red": {
            "primary-color": "#195684",
            "secondary-color": "#932c1c",
        },
        "blue-green": {
            "primary-color": "#195684",
            "secondary-color": "#28803f",
        },
        "green-blue": {
            "primary-color": "#1a602d",
            "secondary-color": "#2a5ea4",
        },
        "greens": {
            "primary-color": "#193e1c",
            "secondary-color": "#347a3a",
        },
        "blues": {
            "primary-color": "hsl(217, 70%, 20%)",
            "secondary-color": "hsl(216, 42%, 47%)",
        },
    }

    scheme = "blue-red"
    if "palette" in theme_opts["options"].keys():
        if theme_opts["options"]["palette"]:
            selected_palette = theme_opts["options"]["palette"]
            if selected_palette in color_schemes.keys():
                scheme = theme_opts["options"]["palette"]
            else:
                log.warning(
                    "Selected palette " + selected_palette + " not found in color schemes. Using default scheme."
                )

    if "primary-color" not in theme_opts["options"].keys():
        theme_opts["options"]["primary-color"] = color_schemes[scheme]["primary-color"]

    if "secondary-color" not in theme_opts["options"].keys():
        theme_opts["options"]["secondary-color"] = color_schemes[scheme]["secondary-color"]

    log.info("Using prebuilt CSS theme: " + theme_name + " with options: " + str(theme_opts))

    with open(src, "r", encoding="utf-8") as theme_file:
        filedata = theme_file.read()

        filedata = re.sub(r"sourceMappingURL=[^\s]*", r"sourceMappingURL=theme.css.map", filedata)

        regular_vars = {k: v for k, v in theme_opts["options"].items() if "-dark" not in k}
        if regular_vars:
            filedata += "\n/* generated from pub variables */\n:root:not(.dark-mode) {"
            for key, value in regular_vars.items():
                filedata += "--{}: {};".format(key, value)
            filedata += "}"

        dark_vars = {k.replace("-dark", ""): v for k, v in theme_opts["options"].items() if "-dark" in k}
        if dark_vars:
            filedata += "\n/* generated from pub variables */\n:root.dark-mode {"
            for key, value in dark_vars.items():
                filedata += "--{}: {};".format(key, value)
            filedata += "}"

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w+", encoding="utf-8") as file:
            file.write(filedata)

    if os.path.exists(src + ".map"):
        shutil.copy(src + ".map", dest + ".map")

    for file in ["print-worksheet.css", "print-worksheet.css.map"]:
        src = os.path.join(css_src, file)
        dest = os.path.join(css_dest, file)
        if os.path.exists(src):
            shutil.copy(src, dest)


def _build_custom_theme(xml, theme_name, theme_opts, tmp_dir):
    ptx_path = common.get_ptx_path()
    script = os.path.join(ptx_path, "script", "cssbuilder", "cssbuilder.mjs")
    css_dest = os.path.join(tmp_dir, "_static", "pretext", "css")

    if theme_name == "custom":
        theme_opts["options"]["entry-point"] = os.path.join(
            common.get_source_path(xml), theme_opts["options"]["entry-point"]
        )

    error_message = "Node.js is required to build themes other than default-modern. Make sure it is installed and in your PATH. Then do 'npm install' in the pretext/script/cssbuilder directory. https://pretextbook.org/doc/guide/html/node-and-npm.html"
    try:
        import subprocess, json

        node_exec_cmd = common.get_executable_cmd("node")
        full_name = "theme-{}".format(theme_name)
        log.info("Building custom css theme: " + full_name)
        log.debug("Theme options:" + json.dumps(theme_opts))
        result = subprocess.run(
            node_exec_cmd + [script, "-t", full_name, "-o", css_dest, "-c", json.dumps(theme_opts)],
            capture_output=True,
            timeout=60,
        )
        if result.stdout:
            log.debug(result.stdout.decode().rstrip())
        if result.stderr:
            error_message = result.stderr.decode()
            raise Exception("Failed to build custom theme")
    except Exception as e:
        log.error(error_message)
        raise e


def check_color_contrast(color1, color2):
    try:
        import coloraide

        contrast = coloraide.Color(color1).contrast(color2, method="wcag21")
        if contrast < 4.5:
            log.warning(
                "Color "
                + color1
                + " does not have enough contrast with expected background color "
                + color2
                + ". Contrast ratio is "
                + str(contrast)
                + " but should be at least 4.5. Adjust your publisher file html/css/variables to ensure sufficient contrast."
            )
    except ImportError:
        log.warning(
            "The coloraide module is not available and is necessary for checking color contrast. Install it with 'pip install coloraide' or by using the requirements.txt file."
        )


def build_or_copy_theme(xml, pub_var_dict, tmp_dir):
    theme_name = common.get_publisher_variable(pub_var_dict, "html-theme-name")
    theme_opts_json = common.get_publisher_variable(pub_var_dict, "html-theme-options")
    import json

    theme_opts = json.loads(theme_opts_json)

    for var, check_color in theme_opts["contrast-checks"].items():
        if var in theme_opts["options"]:
            check_color_contrast(theme_opts["options"][var], check_color)

    use_prerolled = False
    if "-legacy" in theme_name:
        use_prerolled = True
    elif theme_name == "default-modern":
        try:
            common.get_executable_cmd("node")
            if not os.path.exists(os.path.join(common.get_ptx_path(), "script", "cssbuilder", "node_modules")):
                log.info(
                    "CSSBuilder packages not installed. Relying on prebuilt default-modern. To fix this, run 'npm install' in the pretext/script/cssbuilder directory. https://pretextbook.org/doc/guide/html/node-and-npm.html"
                )
                use_prerolled = True
        except Exception as e:
            log.info("Node.js not available. Relying on prebuilt default-modern.")
            use_prerolled = True

    if use_prerolled:
        _move_prebuilt_theme(theme_name, theme_opts, tmp_dir)
    else:
        _build_custom_theme(xml, theme_name, theme_opts, tmp_dir)


def update_theme(xml_source, publication_file, stringparams, dest_dir):
    tmp_dir = common.get_temporary_directory()
    pub_vars = common.get_publisher_variable_report(xml_source, publication_file, stringparams)
    build_or_copy_theme(xml_source, pub_vars, tmp_dir)
    common.copy_build_directory(tmp_dir, dest_dir)


def html(xml, pub_file, stringparams, xmlid_root, file_format, extra_xsl, out_file, dest_dir, ext_rs_methods):

    stringparams = stringparams.copy()

    log_time_info = stringparams.get("debug.profile", False) == "yes"
    time_logger = Stopwatch("html()", log_time_info)

    generated_abs, external_abs = common.get_managed_directories(xml, pub_file)
    data_dir = common.get_source_directories(xml)

    tmp_dir = common.get_temporary_directory()

    pub_vars = common.get_publisher_variable_report(xml, pub_file, stringparams)
    include_static_files = common.get_publisher_variable(pub_vars, "b-cdn-resources") != "true"
    include_generated_svgs = common.get_publisher_variable(pub_vars, "portable-html") != "yes"
    time_logger.log("pubvars loaded")

    if include_static_files:
        _place_runestone_services(tmp_dir, stringparams, ext_rs_methods)
    else:
        _cdn_runestone_services(stringparams, ext_rs_methods)
    time_logger.log("runestone placed")

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    if file_format == "scorm":
        stringparams["html.scorm"] = "yes"
    if extra_xsl:
        extraction_xslt = extra_xsl
    else:
        extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-html.xsl")

    common.copy_managed_directories(tmp_dir, external_abs=external_abs, generated_abs=generated_abs, data_abs=data_dir)
    time_logger.log("managed directories copied")

    if include_static_files:
        copy_html_js(tmp_dir)
        build_or_copy_theme(xml, pub_vars, tmp_dir)
        time_logger.log("css/js copied")

    log.info("converting {} to HTML in {}".format(xml, tmp_dir))
    common.xsltproc(extraction_xslt, xml, None, tmp_dir, stringparams)
    time_logger.log("xsltproc complete")

    if common.get_publisher_variable(pub_vars, "host-platform") == "runestone":
        log.info("building Runestone page template for {} in {}".format(xml, tmp_dir))
        runestone_page_template_xslt = os.path.join(common.get_ptx_xsl_path(), "extract-runestone-page-template.xsl")
        common.xsltproc(runestone_page_template_xslt, xml, None, tmp_dir, stringparams)
        time_logger.log("runestone page template extraction complete")

    if not (include_generated_svgs):
        shutil.rmtree(os.path.join(tmp_dir, "generated", "latex-image"), ignore_errors=True)

    if file_format == "html":
        common.copy_build_directory(tmp_dir, dest_dir)
    elif file_format == "zip" or file_format == "scorm":
        with common.working_directory(tmp_dir):
            zip_file = "html-output.zip"
            log.info("packaging a zip file temporarily as {}".format(os.path.join(tmp_dir, zip_file)))
            with zipfile.ZipFile(zip_file, mode="w", compression=zipfile.ZIP_DEFLATED) as epub:
                for root, dirs, files in os.walk("."):
                    for name in files:
                        if name != zip_file:
                            epub.write(os.path.join(root, name))
            derivedname = common.get_output_filename(xml, out_file, dest_dir, ".zip")
            shutil.copy2(zip_file, derivedname)
            log.info("zip file of HTML output deposited as {}".format(derivedname))
    else:
        raise ValueError("PTX:BUG: HTML file format not recognized")

    time_logger.log("build completed")


def _inline_reveal_resources(html_file, local_dir, reveal_root):

    #

    import base64
    import mimetypes
    import re
    import urllib.parse

    import requests

    font_types = {
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
    }

    def fetch(url):
        base, dot, extension = url.rpartition(".")
        candidates = ["{}.min.{}".format(base, extension), url] if dot else [url]
        for candidate in candidates:
            response = requests.get(candidate, timeout=30)
            if response.status_code == 200:
                return response
        raise OSError("failed to retrieve {} while embedding slideshow resources".format(url))

    def embed_css_urls(css_text, css_url):
        def replacement(match):
            reference = match.group(1).strip("'\" ")
            if reference.startswith(("data:", "http:", "https:", "//", "#")):
                return match.group(0)
            target = urllib.parse.urljoin(css_url, reference)
            response = requests.get(target, timeout=30)
            if response.status_code != 200:
                log.warning("could not retrieve {} referenced by an embedded stylesheet".format(target))
                return match.group(0)
            extension = "." + target.rpartition(".")[2].lower()
            mime = font_types.get(extension) or mimetypes.guess_type(target)[0] or "application/octet-stream"
            encoded = base64.b64encode(response.content).decode("ascii")
            return "url(data:{};base64,{})".format(mime, encoded)

        return re.sub(r"url\(([^)]+)\)", replacement, css_text)

    def guard(text, element):
        sequence = "</{}".format(element)
        if sequence in text.lower():
            log.warning("escaping a premature closing sequence while embedding a {} element".format(element))
            text = re.sub("</{}".format(element), "<\\\\/{}".format(element), text, flags=re.I)
        return text

    with open(html_file, "r", encoding="utf-8") as page_file:
        page = page_file.read()

    for tag in re.findall(r'<link[^>]*rel="stylesheet"[^>]*>', page):
        href_match = re.search(r'href="([^"]*)"', tag)
        if not href_match:
            continue
        href = href_match.group(1)
        if href.startswith(reveal_root):
            response = fetch(href)
            css = embed_css_urls(response.text, response.url)
        elif href.startswith(("http:", "https:", "//")):
            response = requests.get(href, timeout=30)
            if response.status_code != 200:
                log.warning("could not retrieve {} for embedding".format(href))
                continue
            css = embed_css_urls(response.text, response.url)
        else:
            with open(os.path.join(local_dir, href), "r", encoding="utf-8") as css_file:
                css = css_file.read()
        page = page.replace(tag, "<style>\n{}\n</style>".format(guard(css, "style")))

    for tag, src in re.findall(r'(<script src="([^"]*)"></script>)', page):
        if src.startswith(reveal_root):
            js = fetch(src).text
        elif not src.startswith(("http:", "https:", "//")):
            with open(os.path.join(local_dir, src), "r", encoding="utf-8") as js_file:
                js = js_file.read()
        else:
            continue
        page = page.replace(tag, "<script>\n{}\n</script>".format(guard(js, "script")))

    with open(html_file, "w", encoding="utf-8") as page_file:
        page_file.write(page)


def revealjs(xml, pub_file, stringparams, xmlid_root, file_format, extra_xsl, out_file, dest_dir):

    stringparams = stringparams.copy()

    generated_abs, external_abs = common.get_managed_directories(xml, pub_file)

    tmp_dir = common.get_temporary_directory()

    if pub_file:
        stringparams["publisher"] = pub_file
    if xmlid_root:
        stringparams["subtree"] = xmlid_root
    if extra_xsl:
        extraction_xslt = extra_xsl
    else:
        extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-revealjs.xsl")

    common.copy_managed_directories(tmp_dir, external_abs=external_abs, generated_abs=generated_abs)

    copy_html_js(tmp_dir)

    css_src = os.path.join(common.get_ptx_path(), "css", "dist", "pretext-reveal.css")
    css_dest = os.path.join(tmp_dir, "_static", "pretext", "css", "pretext-reveal.css")
    with open(css_src, "r", encoding="utf-8") as theme_file:
        filedata = theme_file.read()
        os.makedirs(os.path.dirname(css_dest), exist_ok=True)
        with open(css_dest, "w+", encoding="utf-8") as file:
            file.write(filedata)

    pub_vars = common.get_publisher_variable_report(xml, pub_file, stringparams)
    math_source = common.get_publisher_variable(pub_vars, "reveal-math-source")
    if math_source == "embedded":
        math_tmp_dir = common.get_temporary_directory()
        math_representations = os.path.join(math_tmp_dir, "math-representations-svg.xml")
        speech_representations = os.path.join(math_tmp_dir, "math-representations-speech.xml")
        msg = "converting raw LaTeX from {} into clean {} format placed into {}"
        log.debug(msg.format(xml, "svg", math_representations))
        mathjax_latex(xml, pub_file, math_representations, None, "svg", False)
        log.debug(msg.format(xml, "speech", speech_representations))
        mathjax_latex(xml, pub_file, speech_representations, None, "speech", False)
        stringparams["mathfile"] = math_representations.replace(os.sep, "/")
        stringparams["speechfile"] = speech_representations.replace(os.sep, "/")

    log.info("converting {} to HTML in {}".format(xml, tmp_dir))
    derivedname = common.get_output_filename(xml, out_file, dest_dir, ".html")
    common.xsltproc(extraction_xslt, xml, derivedname, tmp_dir, stringparams)
    resources_host = common.get_publisher_variable(pub_vars, "reveal-resources-host")
    if resources_host == "embedded":
        reveal_root = common.get_publisher_variable(pub_vars, "reveal-root")
        log.info("embedding reveal.js resources for a single-file slideshow")
        _inline_reveal_resources(derivedname, tmp_dir, reveal_root)
    common.copy_build_directory(tmp_dir, dest_dir)


def assembly(xml, pub_file, stringparams, out_file, dest_dir, method):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file
    if method in ["static", "dynamic", "pg-problems"]:
        stringparams["debug.assembly.exercise"] = method
    elif method == "version":
        stringparams["assembly.version-only"] = "yes"
    elif method == "assembly-id":
        stringparams["assembly.assembly-id-only"] = "yes"
    else:
        log.error("assembly method {} not recognized".format(method))
    extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "utilities", "pretext-enhanced-source.xsl")
    derivedname = common.get_output_filename(xml, out_file, dest_dir, ".xml")
    log.info("converting {} to enhanced (pre-processed) PreTeXt source as {}".format(xml, derivedname))
    common.xsltproc(extraction_xslt, xml, derivedname, None, stringparams)


def assembly_internal(xml, pub_file, stringparams, method):
    stringparams = stringparams.copy()
    if pub_file:
        stringparams["publisher"] = pub_file
    if method in ["static", "dynamic", "pg-problems"]:
        stringparams["debug.assembly.exercise"] = method
    elif method == "version":
        stringparams["assembly.version-only"] = "yes"
    elif method == "assembly-id":
        stringparams["assembly.assembly-id-only"] = "yes"
    else:
        log.error("assembly method {} not recognized".format(method))
    extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "utilities", "pretext-enhanced-source.xsl")
    log.debug("converting {} to enhanced (pre-processed) PreTeXt source for internal use".format(xml))
    return common.xsltproc(extraction_xslt, xml, None, None, stringparams)


def get_latex_style(xml, pub_file, stringparams):
    pub_vars = common.get_publisher_variable_report(xml, pub_file, stringparams)
    journal_name = common.get_publisher_variable(pub_vars, "journal-name")
    pub_latex_style = common.get_publisher_variable(pub_vars, "latex-style")
    if len(journal_name) > 0:
        journal_info = get_journal_info(journal_name)
        log.debug(f"Journal Info: {journal_info}")
        stringparams["journal.texstyle.file"] = journal_info.get("texstyle-file", "")
        latex_style = journal_info.get("latex-style", "")
        if len(latex_style) == 0:
            msg = "The journal name {} in your publication file is invalid or does not correspond to a valid latex-style.  Using the default LaTeX style instead."
            log.warning(msg.format(journal_name))
            latex_style = pub_latex_style
        if len(pub_latex_style) > 0 and pub_latex_style != latex_style:
            msg = "Your publication file specifies a latex-style of {}, but a journal name of {}.  Building with the latex style {} which matches that journal instead."
            log.warning(msg.format(pub_latex_style, journal_name, latex_style))
    else:
        latex_style = pub_latex_style
    return latex_style


def latex_package(xml, pub_file, stringparams, dest_dir):
    pub_vars = common.get_publisher_variable_report(xml, pub_file, stringparams)
    journal_name = common.get_publisher_variable(pub_vars, "journal-name")
    if journal_name:
        tmp_dir = common.get_temporary_directory()
        dest_dir = os.path.join(dest_dir, journal_name)
        place_latex_package_files(dest_dir, journal_name, tmp_dir)
        log.info("latex package files downloaded to " + dest_dir)
    else:
        log.warning("No journal name found in publication file, so no latex package files downloaded.")


def latex(xml, pub_file, stringparams, extra_xsl, out_file, dest_dir, latex_format):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file

    latex_style = get_latex_style(xml, pub_file, stringparams)

    latex_format_stylesheets = {
        "latex": "pretext-latex.xsl",
        "beamer": "pretext-beamer.xsl",
    }

    if extra_xsl:
        extraction_xslt = extra_xsl
        if latex_style:
            log.warning("Ignoring the publisher file's latex-style in favor of the extra XSL specified.")
    elif latex_style and (latex_format == "latex"):
        log.debug("Using LaTeX style: {}".format(latex_style))
        extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "latex", f"pretext-latex-{latex_style}.xsl")
    else:
        extraction_xslt = os.path.join(common.get_ptx_xsl_path(), latex_format_stylesheets[latex_format])
    derivedname = common.get_output_filename(xml, out_file, dest_dir, ".tex")
    log.info("converting {} to LaTeX as {}".format(xml, derivedname))
    common.xsltproc(extraction_xslt, xml, derivedname, None, stringparams)


def fo(xml, pub_file, stringparams, out_file, dest_dir):

    stringparams = stringparams.copy()

    if pub_file:
        stringparams["publisher"] = pub_file

    extraction_xslt = os.path.join(common.get_ptx_xsl_path(), "pretext-fo.xsl")
    derivedname = common.get_output_filename(xml, out_file, dest_dir, ".fo")
    companion_dir = os.path.dirname(os.path.abspath(derivedname))
    log.info("converting {} to XSL-FO as {}".format(xml, derivedname))
    common.xsltproc(extraction_xslt, xml, derivedname, companion_dir, stringparams)


def _latex_compile(latex_cmd, log_file, source_name, max_passes=10, capture_output=False):
    run_kwargs = {"stdout": subprocess.PIPE, "encoding": "utf-8"} if capture_output else {}
    result = subprocess.run(latex_cmd, **run_kwargs)
    pass_count = 1
    while (
        result.returncode == 0
        and os.path.isfile(log_file)
        and "Rerun to get" in open(log_file, encoding="utf-8", errors="replace").read()
        and pass_count < max_passes
    ):
        log.info("Rerunning LaTeX for {} (pass {})".format(source_name, pass_count + 1))
        result = subprocess.run(latex_cmd, **run_kwargs)
        pass_count += 1
    if pass_count == max_passes and result.returncode == 0:
        log.warning(
            "LaTeX compilation of {} required {} passes and may not have converged.".format(source_name, max_passes)
        )
        result.returncode = 1
    return result


def pdf(xml, pub_file, stringparams, extra_xsl, out_file, dest_dir, method, outputs, latex_format):
    outputs_options = ["pdf-only", "prebuild", "all", "all-clean"]
    if outputs not in outputs_options:
        log.warning(
            "You requested outputs of {}, but this is not a recognized option.  Defaulting to 'pdf-only'.".format(
                outputs
            )
        )
    stringparams = stringparams.copy()

    generated_abs, external_abs = common.get_managed_directories(xml, pub_file)
    data_dir = common.get_source_directories(xml)

    if pub_file:
        stringparams["publisher"] = pub_file
    tmp_dir = common.get_temporary_directory()

    latex(xml, pub_file, stringparams, extra_xsl, None, tmp_dir, latex_format)

    basename = os.path.splitext(os.path.split(xml)[1])[0]
    sourcename = basename + ".tex"
    pdfname = basename + ".pdf"

    common.copy_managed_directories(tmp_dir, external_abs=external_abs, generated_abs=generated_abs, data_abs=data_dir)

    pub_vars = common.get_publisher_variable_report(xml, pub_file, stringparams)
    journal_name = common.get_publisher_variable(pub_vars, "journal-name")
    if journal_name:
        place_latex_package_files(tmp_dir, journal_name, os.path.join(generated_abs, "latex-packages"))

    if outputs == "all-clean" or outputs == "prebuild":
        common.copy_build_directory(tmp_dir, dest_dir)
        if outputs == "prebuild":
            return

    with common.working_directory(tmp_dir):
        latex_key = common.get_deprecated_tex_fallback(method)
        latex_exec_cmd = common.get_executable_cmd(latex_key)
        latex_cmd = latex_exec_cmd + ["-halt-on-error", sourcename]
        logname = basename + ".log"
        result = _latex_compile(latex_cmd, logname, sourcename)
        if result.returncode != 0:
            raise OSError(
                "the LaTeX compilation of {} failed, so no PDF was produced.  Consult {} for the errors reported by the LaTeX engine".format(
                    sourcename, logname
                )
            )

        if outputs == "all":
            common.copy_build_directory(tmp_dir, dest_dir)
        else:
            if out_file:
                shutil.copy2(pdfname, out_file)
            else:
                shutil.copy2(pdfname, dest_dir)


def _pdf_fo_accessibility_repairs(pdfname):
    try:
        import fitz
    except ImportError:
        log.warning(
            "the 'pyMuPDF' module is not installed, so PDF link annotations lack the alternate descriptions PDF/UA requires"
        )
        return

    import re

    doc = fitz.open(pdfname)
    alternate_text = {}

    def harvest(node_type, node_value):
        if node_type == "xref":
            node = int(node_value.split()[0])
            kids = doc.xref_get_key(node, "Kids")
            nums = doc.xref_get_key(node, "Nums")
        elif node_type == "dict":
            kids_match = re.search(r"/Kids\s*(\[[^\]]*\])", node_value)
            kids = ("array", kids_match.group(1)) if kids_match else ("null", "null")
            nums_match = re.search(r"/Nums\s*(\[[^\]]*\])", node_value)
            nums = ("array", nums_match.group(1)) if nums_match else ("null", "null")
        else:
            return
        if kids[0] == "array":
            for reference in re.findall(r"(\d+)\s+0\s+R", kids[1]):
                harvest("xref", reference + " 0 R")
        if nums[0] == "array":
            for index, element in re.findall(r"(\d+)\s+(\d+)\s+0\s+R", nums[1]):
                alt = doc.xref_get_key(int(element), "Alt")
                if alt[0] == "string":
                    alternate_text[int(index)] = alt[1]

    struct_root = doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")
    if struct_root[0] == "xref":
        harvest(*doc.xref_get_key(int(struct_root[1].split()[0]), "ParentTree"))
    additions = 0
    for page in doc:
        for link in page.links():
            xref = link["xref"]
            if doc.xref_get_key(xref, "Contents")[0] != "null":
                continue
            description = None
            struct_parent = doc.xref_get_key(xref, "StructParent")
            if struct_parent[0] == "int":
                description = alternate_text.get(int(struct_parent[1]))
            if description is None:
                description = link.get("uri") or "internal cross-reference"
            doc.xref_set_key(xref, "Contents", fitz.get_pdf_str(description))
            additions += 1
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "S")[1] == "/Note" and doc.xref_get_key(xref, "ID")[0] == "null":
            doc.xref_set_key(xref, "ID", "(Note-{})".format(xref))
            additions += 1

    struct_root = doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")
    if struct_root[0] == "xref":
        root_xref = int(struct_root[1].split()[0])
        root_kids = doc.xref_get_key(root_xref, "K")
        if root_kids[0] == "xref":
            document_element = int(root_kids[1].split()[0])
        elif root_kids[0] == "array":
            document_refs = re.findall(r"(\d+)\s+0\s+R", root_kids[1])
            document_element = int(document_refs[0]) if document_refs else None
        else:
            document_element = None

        def tree_node(node_type, node_value):
            if node_type == "xref":
                node = int(node_value.split()[0])
                nums = doc.xref_get_key(node, "Nums")
                kids = doc.xref_get_key(node, "Kids")
                return (nums[1] if nums[0] == "array" else None, kids[1] if kids[0] == "array" else None)
            nums = re.search(r"/Nums\s*(\[.*\])", node_value)
            kids = re.search(r"/Kids\s*(\[[^\]]*\])", node_value)
            return (nums.group(1) if nums else None, kids.group(1) if kids else None)

        def resolve_leaf(node_type, node_value):
            nums, kids = tree_node(node_type, node_value)
            if kids:
                refs = re.findall(r"(\d+)\s+0\s+R", kids)
                if refs:
                    return resolve_leaf("xref", refs[-1] + " 0 R")
            return int(node_value.split()[0]) if node_type == "xref" else None

        def tree_max_key(node_type, node_value):
            nums, kids = tree_node(node_type, node_value)
            keys = [-1]
            if nums:
                keys += [int(k) for k in re.findall(r"(\d+)\s+(?:\d+\s+0\s+R|<<|\[)", nums)]
            if kids:
                keys += [tree_max_key("xref", r + " 0 R") for r in re.findall(r"(\d+)\s+0\s+R", kids)]
            return max(keys)

        parent_tree = doc.xref_get_key(root_xref, "ParentTree")
        leaf = resolve_leaf(*parent_tree) if document_element is not None else None
        if leaf is not None:
            next_key = doc.xref_get_key(root_xref, "ParentTreeNextKey")
            key = int(next_key[1]) if next_key[0] == "int" else tree_max_key(*parent_tree) + 1

            new_links = []
            for page in doc:
                page_xref = page.xref
                for link in page.links():
                    annot = link["xref"]
                    if doc.xref_get_key(annot, "Subtype")[1] != "/Link":
                        continue
                    if doc.xref_get_key(annot, "StructParent")[0] == "int":
                        continue
                    link_element = doc.get_new_xref()
                    objr = "<</Type/OBJR/Pg {} 0 R/Obj {} 0 R>>".format(page_xref, annot)
                    doc.update_object(
                        link_element,
                        "<</Type/StructElem/S/Link/P {} 0 R/Pg {} 0 R/K {}>>".format(document_element, page_xref, objr),
                    )
                    doc.xref_set_key(annot, "StructParent", str(key))
                    new_links.append((key, link_element))
                    key += 1
                    additions += 1

            if new_links:
                new_refs = " ".join("{} 0 R".format(x) for _, x in new_links)
                k_entry = doc.xref_get_key(document_element, "K")
                if k_entry[0] == "array":
                    document_kids = k_entry[1].rstrip()[:-1] + " " + new_refs + "]"
                elif k_entry[0] == "xref":
                    document_kids = "[{} {}]".format(k_entry[1], new_refs)
                else:
                    document_kids = "[{}]".format(new_refs)
                doc.xref_set_key(document_element, "K", document_kids)
                nums = " ".join("{} {} 0 R".format(k, x) for k, x in new_links)
                leaf_nums = doc.xref_get_key(leaf, "Nums")
                existing = leaf_nums[1].strip()[1:-1].strip() if leaf_nums[0] == "array" else ""
                doc.xref_set_key(leaf, "Nums", "[{}]".format((existing + " " + nums).strip()))
                leaf_limits = doc.xref_get_key(leaf, "Limits")
                low = (
                    re.findall(r"-?\d+", leaf_limits[1])[0]
                    if (leaf_limits[0] == "array" and existing)
                    else str(new_links[0][0])
                )
                doc.xref_set_key(leaf, "Limits", "[{} {}]".format(low, new_links[-1][0]))
                doc.xref_set_key(root_xref, "ParentTreeNextKey", str(key))

    if additions > 0:
        doc.saveIncr()
    doc.close()
    log.debug("made {} accessibility repairs in {}".format(additions, pdfname))


def _downgrade_svg2_for_batik(directory):

    import glob, copy, re, colorsys
    import lxml.etree as ET

    SVG = "http://www.w3.org/2000/svg"
    XLINK = "http://www.w3.org/1999/xlink"
    XHTML = "http://www.w3.org/1999/xhtml"
    ET.register_namespace("xlink", XLINK)
    tag = lambda t: f"{{{SVG}}}{t}"
    xhref = f"{{{XLINK}}}href"
    POSITIONS = ("marker-start", "marker-end", "marker-mid")
    _URL_RE = re.compile(r"^url\(#([^)]+)\)$")
    _HSL_RE = re.compile(r"hsl\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*\)")
    _RGB_RE = re.compile(r"rgb\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)")
    _FILTER_FN_RE = re.compile(r"(filter\s*:)\s*([^;{}]+)")
    _TRANS_RE = re.compile(r"translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)")

    def parse_style(el):
        d = {}
        for part in (el.get("style") or "").split(";"):
            k, sep, v = part.partition(":")
            if sep:
                d[k.strip()] = v.strip()
        return d

    def emit_style(d):
        return ";".join(f"{k}:{v}" for k, v in d.items())

    def get_prop(el, prop):
        return parse_style(el).get(prop) or el.get(prop)

    def _hsl_to_hex(m):
        h, s, l = float(m.group(1)) / 360, float(m.group(2)) / 100, float(m.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))

    def _rgb_to_hex(m):
        return "#{:02x}{:02x}{:02x}".format(
            round(float(m.group(1))), round(float(m.group(2))), round(float(m.group(3)))
        )

    def _strip_filter_fn(m):
        val = m.group(2).strip()
        if "(" in val and not val.startswith("url("):
            return m.group(1) + "none"
        return m.group(0)

    def has_context_paint(marker):
        return any(
            get_prop(el, attr) in ("context-stroke", "context-fill")
            for el in marker.iter()
            for attr in ("fill", "stroke")
        )

    def is_svg2_marker(m):
        return has_context_paint(m) or m.get("orient") == "auto-start-reverse"

    def resolve_paint(v, stroke, fill):
        if v == "context-stroke":
            return stroke
        if v == "context-fill":
            return fill
        return v

    def make_marker(orig, new_id, stroke, fill, rotate):
        m = copy.deepcopy(orig)
        m.set("id", new_id)
        if m.get("orient") == "auto-start-reverse":
            m.set("orient", "auto")
        if rotate:
            g = ET.Element(tag("g"))
            g.set("transform", f"rotate(180 {m.get('refX', '0')} {m.get('refY', '0')})")
            for child in list(m):
                m.remove(child)
                g.append(child)
            m.append(g)
        for el in m.iter():
            sty = parse_style(el)
            sty2 = {k: resolve_paint(v, stroke, fill) for k, v in sty.items()}
            if sty2 != sty:
                el.set("style", emit_style(sty2))
            for attr in ("fill", "stroke"):
                v = el.get(attr)
                if v:
                    el.set(attr, resolve_paint(v, stroke, fill))
        return m

    def get_marker_ref(el, pos):
        sty = parse_style(el)
        raw = (sty.get(pos) or el.get(pos) or "").strip()
        mo = _URL_RE.match(raw)
        return mo.group(1) if mo else None

    def set_marker_ref(el, pos, url):
        sty = parse_style(el)
        if pos in sty:
            sty[pos] = url
            el.set("style", emit_style(sty))
        else:
            el.set(pos, url)

    for svg_file in glob.glob(os.path.join(directory, "**", "*.svg"), recursive=True):
        try:
            tree = ET.parse(svg_file)
        except ET.XMLSyntaxError:
            continue
        root = tree.getroot()
        changed = False

        for el in root.iter():
            if not (isinstance(el.tag, str) and el.tag.startswith("{" + SVG + "}")):
                continue
            href = el.get("href")
            if href and el.get(xhref) is None:
                el.set(xhref, href)
                del el.attrib["href"]
                changed = True

        for el in root.iter():
            if el.get("fill") == "transparent":
                el.set("fill", "none")
                changed = True
            for attr in ("fill", "stroke"):
                v = el.get(attr)
                if v:
                    nv = _HSL_RE.sub(_hsl_to_hex, v)
                    nv = _RGB_RE.sub(_rgb_to_hex, nv)
                    if nv != v:
                        el.set(attr, nv)
                        changed = True
        for el in root.iter(tag("style")):
            if not el.text:
                continue
            t = el.text.replace("transparent", "none")
            t = _HSL_RE.sub(_hsl_to_hex, t)
            t = _RGB_RE.sub(_rgb_to_hex, t)
            t = _FILTER_FN_RE.sub(_strip_filter_fn, t)
            if t != el.text:
                el.text = t
                changed = True

        def _em_px(val, font_px):
            try:
                if (val or "").endswith("em"):
                    return float(val[:-2]) * font_px
                if (val or "").endswith("px"):
                    return float(val[:-2])
                return 0.0
            except (ValueError, TypeError):
                return 0.0

        for el in root.iter(tag("text")):
            if el.get("alignment-baseline"):
                del el.attrib["alignment-baseline"]
                changed = True
            db = el.get("dominant-baseline")
            if db in ("central", "middle"):
                sty = parse_style(el)
                fs = sty.get("font-size") or el.get("font-size", "16px")
                try:
                    font_px = float(fs[:-2]) if fs.endswith("px") else 16.0
                except ValueError:
                    font_px = 16.0
                centre = float(el.get("y", 0)) + _em_px(el.get("dy"), font_px)
                el.set("y", f"{centre + 0.35 * font_px:.4g}")
                if "dy" in el.attrib:
                    del el.attrib["dy"]
                for ts in el:
                    if ts.tag == tag("tspan") and "dy" in ts.attrib:
                        del ts.attrib["dy"]
                changed = True
            if db:
                del el.attrib["dominant-baseline"]
                changed = True

        for el in root.iter(tag("text")):
            if el.get("y") is not None:
                continue
            if el.get("dominant-baseline") or el.get("alignment-baseline"):
                continue
            tspans = [c for c in el if c.tag == tag("tspan")]
            if not tspans:
                continue
            ts = tspans[0]
            ts_dy = ts.get("dy", "")
            if not ts_dy:
                continue
            el.set("y", ts_dy)
            del ts.attrib["dy"]
            changed = True

        fo_tag = tag("foreignObject")
        xspan = f"{{{XHTML}}}span"
        for fo in list(root.iter(fo_tag)):
            text = "".join((el.text or "") for el in fo.iter(xspan)).strip()
            if not text:
                continue
            t = fo.get("transform", "")
            m = _TRANS_RE.search(t)
            tx = float(m.group(1)) if m else 0.0
            ty = float(m.group(2)) if m else 0.0
            w = float(fo.get("width", 0))
            h = float(fo.get("height", 18))
            if fo.get("class") == "classTitle":
                x, anchor = tx + w / 2, "middle"
            else:
                x, anchor = tx, "start"
            y = ty + h - 3
            tel = ET.Element(tag("text"))
            tel.set("x", f"{x:.4g}")
            tel.set("y", f"{y:.4g}")
            tel.set("text-anchor", anchor)
            tel.text = text
            parent = fo.getparent()
            if parent is not None:
                idx = list(parent).index(fo)
                parent.remove(fo)
                parent.insert(idx, tel)
            changed = True

        bad = {el.get("id"): el for el in root.iter(tag("marker")) if el.get("id") and is_svg2_marker(el)}
        if bad:
            defs = root.find(tag("defs"))
            if defs is None:
                defs = ET.SubElement(root, tag("defs"))
            key_map = {}
            new_mkrs = {}
            used_ids = set()

            for el in root.iter():
                for pos in POSITIONS:
                    mid = get_marker_ref(el, pos)
                    if not mid or mid not in bad:
                        continue
                    stroke = get_prop(el, "stroke") or "black"
                    fill = get_prop(el, "fill") or "black"
                    rotate = pos == "marker-start" and bad[mid].get("orient") == "auto-start-reverse"
                    key = (mid, stroke, fill, rotate)
                    if key not in key_map:
                        suffix = "start" if rotate else "end"
                        base = f"{mid}-{suffix}"
                        nid = base
                        n = 0
                        while nid in used_ids:
                            n += 1
                            nid = f"{base}-{n}"
                        used_ids.add(nid)
                        key_map[key] = nid
                        new_mkrs[nid] = make_marker(bad[mid], nid, stroke, fill, rotate)
                    set_marker_ref(el, pos, f"url(#{key_map[key]})")

            for m in new_mkrs.values():
                defs.append(m)
            for m in bad.values():
                if m.getparent() is not None:
                    defs.remove(m)
            changed = True

        if changed:
            tree.write(svg_file)


def _math_links_for_batik(math_file):
    import lxml.etree as ET

    svg_namespace = "http://www.w3.org/2000/svg"
    xlink_namespace = "http://www.w3.org/1999/xlink"
    anchor_tag = "{{{}}}a".format(svg_namespace)
    xlink_href = "{{{}}}href".format(xlink_namespace)

    try:
        tree = ET.parse(math_file)
    except (ET.XMLSyntaxError, OSError):
        return
    root = tree.getroot()
    changed = False
    for anchor in root.iter(anchor_tag):
        target = anchor.get("href")
        if target is not None and anchor.get(xlink_href) is None:
            anchor.set(xlink_href, target)
            del anchor.attrib["href"]
            changed = True
    if changed:
        tree.write(math_file)


def pdf_fo(xml, pub_file, stringparams, out_file, dest_dir):
    stringparams = stringparams.copy()

    generated_abs, external_abs = common.get_managed_directories(xml, pub_file)
    data_dir = common.get_source_directories(xml)

    if pub_file:
        stringparams["publisher"] = pub_file
    tmp_dir = common.get_temporary_directory()

    math_representations = os.path.join(tmp_dir, "math-representations-svg.xml")
    mathjax_latex(xml, pub_file, math_representations, None, "svg", True)
    _math_links_for_batik(math_representations)
    stringparams["mathfile"] = math_representations.replace(os.sep, "/")

    speech_representations = os.path.join(tmp_dir, "math-representations-speech.xml")
    mathjax_latex(xml, pub_file, speech_representations, None, "speech", False)
    stringparams["speechfile"] = speech_representations.replace(os.sep, "/")

    fo(xml, pub_file, stringparams, None, tmp_dir)

    basename = os.path.splitext(os.path.split(xml)[1])[0]
    foname = os.path.join(tmp_dir, basename + ".fo")
    pdfname = os.path.join(tmp_dir, basename + ".pdf")

    common.copy_managed_directories(tmp_dir, external_abs=external_abs, generated_abs=generated_abs, data_abs=data_dir)

    fonts_src = os.path.join(common.get_ptx_path(), "fonts")
    shutil.copytree(fonts_src, os.path.join(tmp_dir, "fonts"))

    _downgrade_svg2_for_batik(tmp_dir)

    fop_exec_cmd = common.get_executable_cmd("fop")
    fop_xconf = os.path.join(common.get_ptx_path(), "pretext", "fop.xconf")
    fop_cmd = fop_exec_cmd + ["-c", fop_xconf, "-fo", foname, "-pdf", pdfname]
    log.info("rendering {} as {} with Apache FOP".format(foname, pdfname))
    log.debug("FOP command: {}".format(" ".join(fop_cmd)))
    result = subprocess.run(fop_cmd, cwd=tmp_dir)
    if result.returncode != 0:
        raise OSError("Apache FOP rendering of {} failed".format(foname))

    _pdf_fo_accessibility_repairs(pdfname)

    if out_file:
        shutil.copy2(pdfname, out_file)
    else:
        shutil.copy2(pdfname, dest_dir)


#
#

PI_SOURCE_URI = "{http://pretextbook.org/2020/pretext/internal}source-uri"


def validate(xml_source, pub_file, stringparams, out_file, dest_dir, method, report_form):

    terse = report_form == "terse"
    server = method == "server"
    stringparams = stringparams.copy()

    reportname = common.get_output_filename(xml_source, out_file, dest_dir, "-validation.txt")
    assembled_source = os.path.join(
        os.path.dirname(os.path.abspath(reportname)),
        os.path.splitext(os.path.basename(xml_source))[0] + "-assembled.xml",
    )

    tmp_dir = common.get_temporary_directory()

    source_dir = os.path.dirname(os.path.abspath(xml_source))
    main_file = os.path.basename(xml_source)

    def _stamping_loader(href, parse, encoding=None):
        if parse == "xml":
            elt = ET.parse(href).getroot()
            elt.set(PI_SOURCE_URI, href)
            return elt
        with open(href, "r", encoding=(encoding or "utf-8")) as f:
            return f.read()

    merged_source = os.path.join(tmp_dir, "merged.xml")
    source_tree = ET.parse(xml_source)
    try:
        from lxml import ElementInclude

        ElementInclude.include(source_tree.getroot(), loader=_stamping_loader, max_depth=20)
    except Exception as e:
        log.warning("file attribution of validation problems unavailable ({})".format(e))
        source_tree = ET.parse(xml_source)
        source_tree.xinclude()
    source_tree.getroot().set("{http://www.w3.org/XML/1998/namespace}base", os.path.abspath(xml_source))
    source_tree.write(merged_source, encoding="utf-8", xml_declaration=True)

    stringparams["assembly.file-attribution"] = "yes"
    attributed_source = os.path.join(tmp_dir, "assembled-attributed.xml")
    assembly(merged_source, pub_file, stringparams, attributed_source, None, "version")

    tree_a = ET.parse(attributed_source)
    file_of_a = {}
    current_files = {tree_a.getroot(): main_file}
    for elt in tree_a.iter():
        if not isinstance(elt.tag, str):
            continue
        uri = elt.attrib.pop(PI_SOURCE_URI, None)
        if uri is not None:
            filename = os.path.relpath(uri, start=source_dir)
        else:
            parent = elt.getparent()
            filename = file_of_a.get(parent, main_file)
        file_of_a[elt] = filename
    tree_a.write(assembled_source, encoding="utf-8", xml_declaration=True)
    tree_b = ET.parse(assembled_source)
    a_elements = [e for e in tree_a.iter() if isinstance(e.tag, str)]
    b_elements = [e for e in tree_b.iter() if isinstance(e.tag, str)]
    file_of = {b: file_of_a[a] for a, b in zip(a_elements, b_elements)}
    opening = {}
    for elt in b_elements:
        opening[elt.sourceline] = elt
    with open(assembled_source, encoding="utf-8") as f:
        source_lines = f.readlines()

    schema_dir = os.path.join(common.get_ptx_path(), "schema")
    development_schema = os.path.join(schema_dir, "pretext-dev.rng")
    production_schema = os.path.join(schema_dir, "pretext.rng")
    if not _development_schema_additive(development_schema, production_schema):
        log.warning("the survey of experimental constructs may misclassify until the overlay is repaired")

    def _jing_run(schema_filename):
        if server:
            return _jing_server(schema_filename, assembled_source)
        jing_exec_cmd = common.get_executable_cmd("jing")
        full_cmd = jing_exec_cmd + [schema_filename, assembled_source]
        log.debug("jing command: {}".format(" ".join(full_cmd)))
        result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode > 1:
            log.warning('the "jing" program failed (code {})'.format(result.returncode))
        return result.stdout.splitlines()

    jing_messages = _jing_run(development_schema)
    if jing_messages is None:
        return None
    if not jing_messages:
        log.info("the source validates with no schema errors")
    production_messages = _jing_run(production_schema)

    plus_xsl = os.path.join(common.get_ptx_path(), "schema", "pretext-validation-plus.xsl")
    plus_scratch = os.path.join(tmp_dir, "validation-plus.txt")
    params = {"single.line.output": "yes"}
    common.xsltproc(plus_xsl, assembled_source, plus_scratch, None, params)
    with open(plus_scratch, "r", encoding="utf-8") as f:
        plus_messages = [line.strip() for line in f if line.startswith("PTX:")]

    def _numbered_path(elt, squelch):
        parts = []
        while elt is not None and isinstance(elt.tag, str):
            name = ET.QName(elt).localname
            position = 1 + sum(
                1
                for sib in elt.itersiblings(preceding=True)
                if isinstance(sib.tag, str) and ET.QName(sib).localname == name
            )
            alone = position == 1 and not any(
                isinstance(sib.tag, str) and ET.QName(sib).localname == name for sib in elt.itersiblings()
            )
            if squelch and alone:
                parts.append(name)
            else:
                parts.append("{}[{}]".format(name, position))
            elt = elt.getparent()
        return "/" + "/".join(reversed(parts))

    def _element_at_path(path):
        elt = tree_b.getroot()
        segments = path.strip("/").split("/")
        segment_pattern = re.compile(r"([^\[\]]+)(?:\[(\d+)\])?$")
        first = segment_pattern.match(segments[0])
        if not first or ET.QName(elt).localname != first.group(1):
            return None
        for segment in segments[1:]:
            match = segment_pattern.match(segment)
            if not match:
                return None
            name = match.group(1)
            position = int(match.group(2)) if match.group(2) else 1
            count = 0
            found = None
            for child in elt:
                if isinstance(child.tag, str) and ET.QName(child).localname == name:
                    count += 1
                    if count == position:
                        found = child
                        break
            if found is None:
                return None
            elt = found
        return elt

    def _excerpt(line_number):
        if 0 < line_number <= len(source_lines):
            text = source_lines[line_number - 1].strip()
            if len(text) > 100:
                text = text[:100] + "..."
            return text
        return None

    location = re.compile(r"^.*?:(\d+):(\d+): (.*)$")

    experimental_clusters = []
    if production_messages is not None:
        genuine_positions = set()
        for message in jing_messages:
            match = location.match(message)
            if match:
                genuine_positions.add((int(match.group(1)), int(match.group(2))))
        located = {}
        for message in production_messages:
            match = location.match(message)
            if not match:
                continue
            line_number = int(match.group(1))
            if (line_number, int(match.group(2))) in genuine_positions:
                continue
            near = max((n for n in opening if n <= line_number), default=None)
            if near is None:
                continue
            located.setdefault(opening[near], []).append(match.group(3))
        members_of = {}
        for elt in located:
            top = elt
            ancestor = elt.getparent()
            while ancestor is not None:
                if ancestor in located:
                    top = ancestor
                ancestor = ancestor.getparent()
            members_of.setdefault(top, []).append(elt)
        for top in sorted(members_of, key=lambda e: e.sourceline):
            folded = sum(len(located[member]) for member in members_of[top]) - 1
            headline = located[top][0]
            if headline.startswith("error: "):
                headline = headline[len("error: ") :]
            experimental_clusters.append((top, headline, folded))

    report = []
    banner = "=" * 70

    if not terse:
        report.extend(_validation_report_preamble(development_schema, production_schema, assembled_source))
        report.extend([banner, 'Messages: RELAX-NG schema validation, from "jing"', banner, ""])
    for message in jing_messages:
        match = location.match(message)
        if not match:
            report.append(message)
            continue
        line_number = int(match.group(1))
        body = match.group(3)
        near = max((n for n in opening if n <= line_number), default=None)
        elt = opening[near] if near is not None else None
        filename = file_of.get(elt, main_file)
        if terse:
            path = _numbered_path(elt, False) if elt is not None else ""
            report.append("{}\t{}\t{}\tschema\t{}".format(filename, path, line_number, body))
        else:
            path = _numbered_path(elt, True) if elt is not None else ""
            report.append(body)
            report.append("    file: {}".format(filename))
            report.append("    path: {}".format(path))
            report.append("    line: {}".format(line_number))
            excerpt = _excerpt(line_number)
            if excerpt:
                report.append("    text: {}".format(excerpt))
            report.append("    check: schema")
            report.append("")
    if not terse and not jing_messages:
        report.extend(["(no messages)", ""])

    if not terse:
        report.extend([banner, "Messages: experimental constructs in use", banner, ""])
        report.extend(_experimental_section_preface())
    if production_messages is None:
        if not terse:
            report.extend([
                "(the production-schema examination could not be completed,",
                "so experimental constructs were not surveyed)",
                "",
            ])
    advice_for = {}
    if experimental_clusters and not terse:
        advice_for = _experimental_advice()
    for elt, headline, folded in experimental_clusters:
        filename = file_of.get(elt, main_file)
        line_number = elt.sourceline
        if terse:
            path = _numbered_path(elt, False)
            body = headline
            if folded == 1:
                body += " (plus 1 more message within this construct)"
            elif folded:
                body += " (plus {} more messages within this construct)".format(folded)
            report.append("{}\t{}\t{}\texperimental\t{}".format(filename, path, line_number, body))
        else:
            path = _numbered_path(elt, True)
            report.append(headline)
            if folded == 1:
                report.append("    (1 more message within this construct folded into this entry)")
            elif folded:
                report.append("    ({} more messages within this construct folded into this entry)".format(folded))
            report.append("    file: {}".format(filename))
            report.append("    path: {}".format(path))
            report.append("    line: {}".format(line_number))
            excerpt = _excerpt(line_number)
            if excerpt:
                report.append("    text: {}".format(excerpt))
            paragraphs = advice_for.get(ET.QName(elt).localname)
            if paragraphs is None:
                named = re.match(r'element "([^"]+)"', headline)
                if named:
                    paragraphs = advice_for.get(named.group(1))
            label = "    advice: "
            for paragraph in paragraphs or []:
                report.extend(
                    textwrap.wrap(
                        paragraph,
                        width=70,
                        initial_indent=label,
                        subsequent_indent="            ",
                    )
                )
                label = "            "
            report.append("    check: experimental")
            report.append("")
    if not terse and production_messages is not None and not experimental_clusters:
        report.extend(["(no messages: no experimental constructs are in use)", ""])

    if not terse:
        report.extend([banner, 'Messages: PreTeXt "validation-plus" stylesheet', banner, ""])
    plus_form = re.compile(r"^(PTX:[A-Z]+): (/\S+) (.*)$")
    id_form = re.compile(r"^(.*) \[([a-z0-9-]+)\]$")
    for message in plus_messages:
        match = plus_form.match(message)
        if not match:
            report.append(message)
            continue
        severity, path, body = match.group(1), match.group(2), match.group(3)
        id_match = id_form.match(body)
        if id_match:
            body, check_id = id_match.group(1), id_match.group(2)
        else:
            check_id = "no-validation-message-id-assigned"
        elt = _element_at_path(path)
        filename = file_of.get(elt, main_file)
        line_number = elt.sourceline if elt is not None else ""
        if terse:
            report.append("{}\t{}\t{}\t{}\t{}: {}".format(filename, path, line_number, check_id, severity, body))
        else:
            if elt is not None:
                path = _numbered_path(elt, True)
            report.append("{}: {}".format(severity, body))
            report.append("    file: {}".format(filename))
            report.append("    path: {}".format(path))
            report.append("    line: {}".format(line_number))
            if elt is not None:
                excerpt = _excerpt(elt.sourceline)
                if excerpt:
                    report.append("    text: {}".format(excerpt))
            report.append("    check: {}".format(check_id))
            report.append("")
    if not terse and not plus_messages:
        report.extend(["(no messages)", ""])

    with open(reportname, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    if jing_messages:
        log.info("schema validation raised {} messages".format(len(jing_messages)))
    if experimental_clusters:
        log.info("experimental constructs are in use at {} locations".format(len(experimental_clusters)))
    elif production_messages is not None:
        log.info("no experimental constructs are in use")
    if plus_messages:
        log.info("validation-plus stylesheet raised {} messages".format(len(plus_messages)))
    else:
        log.info("validation-plus stylesheet raised no messages")
    log.info("consolidated validation report in {}".format(reportname))
    log.info("locations refer to the assembled source in {}".format(assembled_source))

    return reportname


def _validation_report_preamble(development_schema, production_schema, assembled_source):

    return [
        "Validation Report",
        "=================",
        "",
        "Three examinations have been made of an assembled version of",
        "your source:",
        "",
        '  (1) "jing" checked conformance with the development RELAX-NG',
        "      schema at",
        "      {}".format(development_schema),
        "      (a schema can only describe parent-child relationships,",
        "      plus the attributes of each element)",
        '  (2) a second "jing" run, against the production schema at',
        "      {}".format(production_schema),
        "      surveyed the experimental constructs in use; that section",
        "      of this report begins with a fuller explanation",
        '  (3) the PreTeXt "validation-plus" stylesheet made checks that',
        "      no RELAX-NG schema could ever express, and offers extra",
        "      advice and explanation besides",
        "",
        "Locations refer to the ASSEMBLED version of your source: your",
        "modular source files have been knitted together, and any version",
        'support has been applied (as elected by a "version" element',
        'within the "source" element of the publication file you',
        "supplied).  In particular, an element excluded from the version",
        "being built cannot raise a message here.  The assembled source",
        "has been deposited at",
        "    {}".format(assembled_source),
        "",
        "Each message locates its problem four ways, and then names",
        "the check that raised it:",
        "",
        "    file:   the source file where the problem lies",
        "    path:   the location within the assembled source",
        "    line:   the line number within the assembled source",
        "    text:   an excerpt of the offending content",
        '    check:  a short name for the check ("schema" for a message',
        '            from "jing", "experimental" for the survey of',
        "            experimental constructs)",
        "",
        'Only "file" points into your own source files.  In particular,',
        '"line" is a line number of the deposited assembled source named',
        "above, never of one of your files.",
        "",
        'To read a "path", count elements of each name.  For example,',
        "",
        "    /pretext/book/chapter[7]/section[2]/p[13]/em[2]",
        "",
        'is the second "em" within the thirteenth "p" (paragraph) of the',
        'second "section" of the seventh "chapter" of the book.  Counts',
        "are of elements with the same name: that paragraph is the",
        'thirteenth "p" of its section, though other elements may precede',
        'it or intervene.  An element without a count, like the "book"',
        "above, is the only element of that name at its location, so a",
        "count would just be clutter.",
        "",
        "",
    ]


def _experimental_advice():
    registry = os.path.join(common.get_ptx_path(), "schema", "experimental-features.xml")
    advice = {}
    try:
        root = ET.parse(registry).getroot()
    except (OSError, ET.XMLSyntaxError) as e:
        log.debug("experimental-features registry unavailable ({})".format(e))
        return advice
    for feature in root.iter("feature"):
        paragraphs = [" ".join("".join(p.itertext()).split()) for p in feature.iter("p")]
        for element in (feature.get("elements") or "").split():
            advice.setdefault(element, paragraphs)
    return advice


def _development_schema_additive(development_schema, production_schema):
    relaxng_namespace = "http://relaxng.org/ns/structure/1.0"
    overlay = ET.parse(development_schema).getroot()
    production = ET.parse(production_schema).getroot()
    production_defines = {define.get("name") for define in production.iter("{{{}}}define".format(relaxng_namespace))}
    offenses = []
    for include in overlay.findall("{{{}}}include".format(relaxng_namespace)):
        if len(include) > 0:
            offenses.append('the "include" carries replacement definitions')
    for define in overlay.findall("{{{}}}define".format(relaxng_namespace)):
        if define.get("combine") == "choice":
            continue
        name = define.get("name")
        if name in production_defines:
            offenses.append('"{}" redefines a production pattern without combine="choice"'.format(name))
    if overlay.findall("{{{}}}start".format(relaxng_namespace)):
        offenses.append('the overlay overrides "start"')
    for offense in offenses:
        log.warning("development schema overlay: {}".format(offense))
    return not offenses


def _experimental_section_preface():

    return [
        "Constructs reported here are part of the development schema, but",
        "not the production schema.  They are experimental: their markup",
        "may change at any time, without the usual deprecation cycle and",
        "automatic conversion of your source.  So this section is not a",
        "list of errors -- it is an inventory of the places where your",
        "source relies on experimental parts of the PreTeXt vocabulary,",
        "so you can weigh the risk, and recognize the cause if one of",
        "these constructs changes underneath you.",
        "",
        "One caution: while genuine errors remain (the previous section),",
        "the two schema examinations may recover from an error in",
        "different ways, and then a few entries here can be echoes of",
        "those errors, rather than experimental constructs.  Once the",
        "previous section is clean, this inventory is exact.",
        "",
    ]


def _jing_server(schema_filename, assembled_source):
    try:
        import requests
    except ImportError:
        raise ImportError(__module_warning.format("requests"))

    server_url = "https://mathgenealogy.org:9000/validate"

    tmp_dir = common.get_temporary_directory()

    schema_dir = os.path.join(common.get_ptx_path(), "schema")
    field_paths = {
        "assembled_source": assembled_source,
        "schema": schema_filename,
        "pf-adapter.rng": os.path.join(schema_dir, "pf-adapter.rng"),
        "pf_schema.rng": os.path.join(schema_dir, "pf_schema.rng"),
        "pf-preamble-adapter.rng": os.path.join(schema_dir, "pf-preamble-adapter.rng"),
    }
    log.info("communicating with validation server at {}".format(server_url))
    data = dict()
    for field, path in field_paths.items():
        with open(path, "r", encoding="utf-8") as file:
            data[field] = file.read()

    if os.path.basename(schema_filename) == "pretext-dev.rng":
        relaxng_namespace = "http://relaxng.org/ns/structure/1.0"
        overlay = ET.parse(schema_filename)
        for include in overlay.iter("{{{}}}include".format(relaxng_namespace)):
            if include.get("href") == "pretext.rng":
                include.set("href", "pretext-production.rng")
        data["schema"] = ET.tostring(overlay.getroot(), encoding="unicode")
        with open(os.path.join(schema_dir, "pretext.rng"), "r", encoding="utf-8") as file:
            data["pretext-production.rng"] = file.read()

    try:
        r = requests.post(server_url, data=data, timeout=60)
    except requests.exceptions.RequestException as e:
        log.error("could not reach the validation server at {} ({})".format(server_url, e))
        log.error("no validation report was produced; retry, or validate with a local method")
        return None

    if r.status_code != 200:
        log.error("the validation server reported an error (code {}): {}".format(r.status_code, r.text.strip()))
        return None

    body = r.text
    if "Report from jing follows:" in body:
        body = body.split("Report from jing follows:", 1)[1]
    elif "no schema violations" in body:
        log.info("the source validates with no schema errors")
        return []
    return body.strip("\n").splitlines()


#
#


def python_version():

    return "{}.{}".format(sys.version_info[0], sys.version_info[1])


def python_module_versions():

    import importlib.metadata

    requirements = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    try:
        with open(requirements, "r", encoding="utf-8") as requirements_file:
            lines = requirements_file.readlines()
    except OSError:
        return "unable to read {}".format(requirements)

    reports = []
    for line in lines:
        line = line.strip()
        if (line == "") or line.startswith("#"):
            continue
        name = re.split(r"[<>=!~;\[\s]", line, maxsplit=1)[0]
        try:
            reports.append("{} {}".format(name, importlib.metadata.version(name)))
        except importlib.metadata.PackageNotFoundError:
            reports.append("{} (not installed)".format(name))
    return ", ".join(reports)


def check_python_version():

    msg = "".join([
        "PreTeXt script/module expects Python 3.10, not Python 2 or older\n",
        "You have Python {}\n",
        "** Try prefixing your command-line with 'python3 ' **",
    ])
    if sys.version_info[0] <= 2:
        raise (OSError(msg.format(python_version())))
    if sys.version_info[:2] < (3, 10):
        log.warning(
            "PreTeXt expects Python 3.10 or newer\nYou have Python {}, and some operations may fail".format(
                python_version()
            )
        )


def copy_html_js(work_dir):

    js_src = os.path.join(common.get_ptx_path(), "js")
    js_dest = os.path.join(work_dir, "_static", "pretext", "js")
    shutil.copytree(js_src, js_dest)


def get_journal_info(journal_name):
    journal_xml = os.path.join(common.get_ptx_path(), "journals", "journals.xml")
    log.debug("Reading list of journals in {}".format(journal_xml))
    journals_tree = ET.parse(journal_xml)
    journals_tree.xinclude()

    try:
        journal = journals_tree.xpath(f"//journal[code='{journal_name.lower()}']")[0]
    except Exception as e:
        log.warning("The journal name {} specified in the publication file is not supported.".format(journal_name))
        return {"latex-style": ""}

    keys = ["name", "code", "publisher"]
    journal_info = {}
    for key in keys:
        element = journal.find(key)
        journal_info[key] = element.text if element is not None else None
    if journal.find("method") is not None:
        for attr in ["latex-style", "texstyle", "dependent"]:
            if attr in journal.find("method").attrib:
                journal_info[attr] = journal.find("method").attrib[attr]

    journal_info["latex-style"] = journal_info.get("latex-style", "texstyle")
    journal_info["texstyle"] = journal_info.get("texstyle", journal_info.get("code"))
    journal_info["dependent"] = journal_info.get("dependent", "no")
    log.debug("Using the journal code {} as the texstyle value.".format(journal_info.get("texstyle")))

    if journal_info["latex-style"] == "texstyle":
        if journal_info["dependent"] == "yes":
            journal_info["texstyle-file"] = "dependents/" + journal_info.get("texstyle") + ".xml"
            log.debug("Using texstyle-file {}.".format(journal_info["texstyle-file"]))
        else:
            journal_info["texstyle-file"] = journal_info.get("texstyle") + ".xml"
            log.debug("Using texstyle-file {}.".format(journal_info["texstyle-file"]))

    return journal_info


def place_latex_package_files(dest_dir, journal_name, cache_dir):
    texstyle_file = get_journal_info(journal_name).get("texstyle-file")
    if texstyle_file is None:
        return
    texstyle_tree = ET.parse(os.path.join(common.get_ptx_path(), "journals", "texstyles", texstyle_file))
    texstyle_file_elements = texstyle_tree.xpath("//required-files/file")
    if not texstyle_file_elements:
        log.debug("No required files found in the texstyle file.")
        return
    journal_code = texstyle_tree.xpath("//metadata/code")[0].text
    cache_dir = os.path.join(cache_dir, journal_code)
    os.makedirs(cache_dir, exist_ok=True)

    for file in texstyle_file_elements:
        file_path = os.path.join(cache_dir, file.attrib["name"])
        if not os.path.exists(file_path):
            log.debug("Downloading required file {} from {}".format(file.attrib["name"], file.attrib["href"]))
            url = file.attrib["href"]
            if url.endswith(".zip"):
                tmp_zip = os.path.join(cache_dir, "tmp.zip")
                common.download_file(url, tmp_zip)
                with zipfile.ZipFile(tmp_zip, "r") as zip_ref:
                    with open(file_path, "wb") as f:
                        f.write(zip_ref.read(file.attrib["path"]))
                os.remove(tmp_zip)
            else:
                common.download_file(url, file_path)
            log.debug("Saved file {} to {}".format(file.attrib["name"], file_path))
        else:
            log.debug("File {} already exists in the generated assets directory.".format(file.attrib["name"]))
        shutil.copy2(file_path, dest_dir)


class Stopwatch:
    def __init__(self, name: str = "", print_log: bool = True):
        self.name = name
        self.print_log = print_log
        self.start_time = time.time()
        self.last_log_time = self.start_time

    def reset(self):
        self.last_log_time = time.time()

    def log(self, timepoint_description: str = ""):
        if self.print_log:
            cur_time = time.time()
            elapsed_time = cur_time - self.start_time
            since_last_log_time = cur_time - self.last_log_time
            self.reset()
            log.info(
                f"** Timing report from {self.name}: {timepoint_description}, {since_last_log_time:.2f}s since last watch reset. {elapsed_time:.2f}s total elapsed time."
            )


#
#

#
#
#
#
#


__xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'


PreTeXtFatal = common.PreTeXtFatal
build_info_message = common.build_info_message
download_file = common.download_file
get_executable_cmd = common.get_executable_cmd
get_managed_directories = common.get_managed_directories
get_platform_host = common.get_platform_host
get_ptx_path = common.get_ptx_path
get_ptx_xsl_path = common.get_ptx_xsl_path
get_publisher_variable_report = common.get_publisher_variable_report
release_temporary_directories = common.release_temporary_directories
set_executables = common.set_executables
set_ptx_path = common.set_ptx_path
verify_input_directory = common.verify_input_directory
xsltproc = common.xsltproc


webwork_to_xml = webwork.webwork_to_xml
webwork_sets = webwork.webwork_sets
pg_macros = webwork.pg_macros


stack_extraction = stack.stack_extraction
