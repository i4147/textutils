# -*- coding: utf-8 -*-

import flask
from flask.json import JSONEncoder
from flask import (
    Flask,
    Response,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    send_from_directory,
    render_template,
    Markup,
)
from werkzeug.utils import secure_filename
import os
import io
import json
import sys
import configparser
import argparse
import traceback
import csv
import uuid
import gc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from timeit import default_timer as timer
from textlab.ocr import *


try:
    parser = argparse.ArgumentParser(description="TextLab Document Processing Server")
    parser.add_argument("config", help="path to config.ini")
    args = parser.parse_args()
    config_file = args.config
except:
    print("ERROR 101: Input error. No : \n{}".format(traceback.format_exc()))
    try:
        config_file = input("Path to config.ini file (Press enter to generate file template): ")
        if len(config_file) == 0:
            raise Exception("No config.ini file path given... genrating template...")
    except:
        print("ERROR 101: Input error. No : \n{}".format(traceback.format_exc()))
        # api_folder = generate_config_file()
        print(
            "API folder and config.ini file template generated at {}.\nEdit the config.ini template before strating the model server".format(
                api_folder
            )
        )
        sys.exit(1)

print("config_file:", config_file)

try:
    config = configparser.ConfigParser()
    config.read(config_file)
    application_name = config["DEFAULT"]["Application"]
    api_home_folder = config["FOLDERS"]["APIHomeFolder"]
    model_folder = config["FOLDERS"]["ModelFolder"]
    if model_folder[0] == "*":
        model_folder = os.path.join(api_home_folder, model_folder[1:])
    dropbox_folder = config["FOLDERS"]["DropBoxFolder"]
    if dropbox_folder[0] == "*":
        dropbox_folder = os.path.join(api_home_folder, dropbox_folder[1:])
    sample_folder = config["FOLDERS"]["SampleFileFolder"]
    if sample_folder[0] == "*":
        sample_folder = os.path.join(api_home_folder, sample_folder[1:])
    temp_folder = config["FOLDERS"]["TempFolder"]
    if temp_folder[0] == "*":
        temp_folder = os.path.join(api_home_folder, temp_folder[1:])
    etl_py_script = os.path.join(model_folder, config["MODEL"]["ETLPyScript"])
    post_process_py_script = os.path.join(model_folder, config["MODEL"]["PostProcessPyScript"])
    host_address = config["API"]["HostAddress"]
    port = config["API"]["Port"]
    static_folder = os.path.join(api_home_folder, config["API"]["Static"])
    html_template_folder = os.path.join(api_home_folder, config["API"]["HTMLTemplates"])
    config_access_key = config["KEYS"]["ConfigAccessKey"]
    api_access_key = config["KEYS"]["APIAccessKey"]
    tesseract_path = config["UTILITY"]["Tesseract"]
    ghostscript_path = config["UTILITY"]["GhostScript"]
except:
    print("Error loading config file !\n{}".format(traceback.format_exc()))

print("-" * 80)
print("TextLab Document Processing Server Confuguarion Profile...")
print("* api_home_folder:", api_home_folder)
print("* static_folder:", static_folder)
print("* html_template_folder:", html_template_folder)
print("* etl_py_script:", etl_py_script)
print("* post_process_py_script:", post_process_py_script)
print("-" * 80)

app = flask.Flask(__name__, template_folder=html_template_folder, static_folder=static_folder)
accepted_file_types = set(["pdf", "png", "jpg", "jpeg", "bmp", "tif", "tiff"])

set_tesseract_path(tesseract_path=tesseract_path, temp_folder=temp_folder)

set_ghostscript_path(ghostscript_path=ghostscript_path, temp_folder=temp_folder, ghostscript_exe="gswin64c.exe")


class custom_json_encoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return round(float(obj), 4)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            iterable = iter(obj)
        except TypeError:
            print("ERROR: \n{}".format(traceback.format_exc()))
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def is_accepted_file_type(file_name):
    return os.path.splitext(file_name)[1][1:].lower() in accepted_file_types


def send_response(responseObj):
    response = flask.jsonify(responseObj)
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST")
    response.headers.add(
        "Access-Control-Allow-Headers",
        "accept,content-type,Origin,X-Requested-With,Content-Type,access_token,Accept,Authorization,source",
    )
    response.headers.add("Access-Control-Allow-Credentials", True)
    return response


@app.after_request
def add_header(response):
    response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
    response.headers["Cache-Control"] = "public, max-age=0"
    return response


@app.route("/")
def index():
    URL = "http://{}:{}/ocr_form".format(host_address, port)
    # print(URL)
    return redirect(URL)


def process_ocr_image_request(request):
    if request.method == "POST":
        print("POST")

        if "file" not in request.files:
            return "No 'file' part found", None

        try:
            osd = request.form["osd"]
        except:
            osd = True

        try:
            aps = request.form["aps"]
        except:
            aps = True

        try:
            lang = request.form["lang"]
        except:
            lang = "eng"

        try:
            dpi = request.form["dpi"]
        except:
            dpi = 90

        try:
            oem = request.form["oem"]
        except:
            oem = 3

        try:
            file = request.files["file"]
            print(file.filename)
            if file.filename == "":
                return "No file found ! ", None

            if file and is_accepted_file_type(file.filename):
                file_name = secure_filename(file.filename)
                file_path = os.path.join(temp_folder, file_name)
                file.save(file_path)

                image = read_image_file(file_path=file_path, show_image=False)
            else:
                return "File Format Not Supported !", None
        except:
            image = None
            return "File Error !", None

        try:
            output = image_to_text(image, osd=osd, aps=aps, lang=lang, dpi=dpi, tessdata_dir=None, os_temp=False)
        except:
            output = None
            return "OCR Error !", None

        try:
            os.remove(file_path)
        except:
            pass

        return output, file_name

    if request.method == "GET":
        return "API ERROR : GET requests not supported.", None


def process_ocr_file_request(request):
    if request.method == "POST":
        # print('POST')

        if "file" not in request.files:
            return "No 'file' part found", None, None

        try:
            osd = request.form["osd"]
        except:
            osd = True

        try:
            aps = request.form["aps"]
        except:
            aps = True

        try:
            lang = request.form["lang"]
        except:
            lang = "eng"

        try:
            dpi = request.form["dpi"]
        except:
            dpi = 90

        try:
            oem = request.form["oem"]
        except:
            oem = "3"

        try:
            file = request.files["file"]
            # print(file.filename)
            if file.filename == "":
                return "No file found ! ", None, None

            if file and is_accepted_file_type(file.filename):
                file_name = secure_filename(file.filename)
                file_path = os.path.join(temp_folder, file_name)
                file.save(file_path)
            else:
                return "File Format Not Supported !", None, None
        except:
            image = None
            return "File Error !", None, None

        try:
            ImagesTable = convert_document_file_to_text(file_path, osd=osd, aps=aps, lang=lang, dpi=dpi, oem=oem)
            pages = ImagesTable["PageNumber"].unique()
            page_count = len(pages)
            output = ImagesTable["Text"].str.cat(na_rep="?", sep="\n\n---[PAGE BREAK]---\n\n")
            del ImagesTable
        except:
            output = None
            return "OCR Error !", None, None

        try:
            os.remove(file_path)
        except:
            pass

        return output, file_name, page_count

    if request.method == "GET":
        return "API ERROR : GET requests not supported.", None, None


@app.route("/ocr", methods=["GET", "POST"])
def ocr():
    try:
        output = process_ocr_request(request)
        return send_response(output)
    except:
        print("API ERROR ! :\n{}\n".format(traceback.format_exc()))
        return send_response("API ERROR: Check input paramaters.")


@app.route("/ocr_form", methods=["GET", "POST"])
def ocr_form():

    LanguageOptions = ""
    for al in available_languages:
        LanguageOptions = LanguageOptions + Markup('<option value="{}">{}</option>\n'.format(al, al))

    if request.method == "POST":
        try:
            start_time = timer()
            output_text, file_name, page_count = process_ocr_file_request(request)
            execute_time = timer() - start_time
            process_time = "{:.3f} s".format(execute_time)
            # print(output)
            result = "PROCESSED"
            input_file_name = file_name
            return render_template(
                "input_form.html",
                InputFileName=input_file_name,
                Result=result,
                OutputText=output_text,
                ProcessTime=process_time,
                PageCount=page_count,
                LanguageOptions=LanguageOptions,
            )
        except:
            print("API ERROR ! :\n{}\n".format(traceback.format_exc()))
            result = "ERROR"
            process_time = None
            return render_template(
                "input_form.html",
                InputFileName="",
                Results=result,
                OutputText="",
                ProcessTime="",
                PageCount="",
                LanguageOptions=LanguageOptions,
            )
        gc.collect()
    else:
        return render_template(
            "input_form.html",
            InputFileName="",
            Results="",
            OutputText="",
            ProcessTime="",
            PageCount="",
            LanguageOptions=LanguageOptions,
        )


@app.route("/test", methods=["GET", "POST"])
def test():
    return "test"


def init():
    global ETL
    global PostProcess
    global available_languages

    available_languages = list_tesseract_languages()

    try:
        import importlib.util

        spec1 = importlib.util.spec_from_file_location("etl_module", etl_py_script)
        etl_module = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(etl_module)
        ETL = etl_module.ETL
    except:
        ETL = lambda DataFrame, variables_setup_dict, etl_parameters: DataFrame
        print("ERROR: \n{}".format(traceback.format_exc()))
        print("No ETL tasks executed...\nInput datset will be not modified...")
    try:
        import importlib.util

        spec2 = importlib.util.spec_from_file_location("post_process_module", post_process_py_script)
        post_process_module = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(post_process_module)
        PostProcess = post_process_module.PostProcess
    except:
        PostProcess = (
            lambda DataFrame, score_result_columns, file_reference, dropbox_folder, temp_folder, post_process_parameters: (
                DataFrame
            )
        )
        print("ERROR: \n{}".format(traceback.format_exc()))
        print("No PostProcess tasks executed...\nScored datset will be not modified...")


if __name__ == "__main__":
    init()
    app.run(host=host_address, port=port, threaded=True, debug=False)
