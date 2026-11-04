# -*- coding: utf-8 -*-

import os
import sys
import gc
import subprocess
import numpy as np
import pandas as pd
import PIL
import PIL.ImageEnhance
import PIL.ImageOps
import PIL.ImageFilter
import PIL.ImageDraw
import uuid
import tempfile
import traceback
import re
import io


def path_to_unix_format(path_string):
    unix_path_string = path_string.replace("\\", "/")
    return unix_path_string


def set_ghostscript_path(ghostscript_path, temp_folder=None, ghostscript_exe="gswin64c.exe"):
    try:
        ghostscript_exe = ghostscript_exe
        os.environ["GHOSTSCRIPT_PATH"] = ghostscript_path
        if temp_folder == None:
            temp_folder = os.path.join(ghostscript_path, "temp")
        os.environ["GHOSTSCRIPT_TEMP"] = temp_folder
        os.environ["GHOSTSCRIPT_APP_COMMAND"] = os.path.join(ghostscript_path, ghostscript_exe)
    except:
        print("ERROR in setting environment variables:\n{}".format(traceback.format_exc()))


def ghostscript(args, decode_output=True):
    output = ""
    error = ""

    command = os.environ["GHOSTSCRIPT_APP_COMMAND"]
    command_parts = [command] + args
    try:
        p = subprocess.Popen(command_parts, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if decode_output:
            output = output.decode()
        error = error.decode()
    except:
        print("Error in running ghostscript\n{}".format(traceback.format_exc()))
    finally:
        try:
            p.kill()
        except:
            pass

    return output, error


def get_pdf_page_count(pdf_file_path):

    pdf_file_path = path_to_unix_format(pdf_file_path)

    page_count_args = [
        "-q",
        "-dNODISPLAY",
        "-c",
        '"({}) (r) file runpdfbegin pdfpagecount = quit"'.format(pdf_file_path),
    ]

    output, error = ghostscript(args=page_count_args)
    print(error)

    try:
        return int(output)
    except:
        print("Error processing output. Row output: {}".format(output))
        return None


def pdf_to_images(
    pdf_file,
    image_format="png",
    dpi=300,
    out_file_prefix="o",
    start_page=1,
    end_page=None,
    pages=None,
    temp_folder=None,
    num_threads=None,
):

    out_file_prefix = out_file_prefix + str(uuid.uuid4())

    pdf_file_path = pdf_file
    pdf_file_path = path_to_unix_format(pdf_file_path)

    if temp_folder == None:
        temp_folder = os.environ["GHOSTSCRIPT_TEMP"]

    out_file_path = os.path.join(temp_folder, "{}%d.png".format(out_file_prefix))
    out_file_path = path_to_unix_format(out_file_path)

    if image_format == "png":
        device = "png16m"
    else:
        print("Image format not supported. Set image_format='png'".format(image_format))
        return None

    page_count = get_pdf_page_count(pdf_file)

    if pages == None:
        if start_page == None and end_page == None:
            page_list = "{}-{}".format(1, page_count)
            pages_to_convert = page_count
        elif start_page != None and end_page != None:
            page_list = "{}-{}".format(start_page, end_page)
            pages_to_convert = end_page - start_page + 1
        elif start_page != None and end_page == None:
            page_list = "{}-{}".format(start_page, page_count)
            pages_to_convert = page_count - start_page + 1
        elif start_page == None and end_page != None:
            page_list = "{}-{}".format(1, end_page)
            pages_to_convert = end_page - start_page
    else:
        page_list = ",".join(str(p) for p in pages)
        pages_to_convert = len(pages)

    if page_count < pages_to_convert:
        print("Invalid page range. Check if pages_to_convert <= page_count".format(image_format))
        return None

    args = [
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-r{}".format(dpi),
        "-sDEVICE={}".format(device),
        "-sPageList={}".format(page_list),
        '-sOutputFile="{}"'.format(out_file_path),
        '"{}"'.format(pdf_file_path),
    ]

    if num_threads != None:
        args = args + ["-dNumRenderingThreads={}".format(num_threads)]

    output, error = ghostscript(args=args)

    file_folder_path = temp_folder
    file_name_prefix = out_file_prefix
    file_name_postfix = ".{}".format(image_format)
    page_range = pages_to_convert
    image_list = read_image_batch(
        file_folder_path,
        file_name_prefix=file_name_prefix,
        file_name_postfix=file_name_postfix,
        page_range=page_range,
        show_image=False,
    )

    return image_list


def read_image_file(file_path, show_image=False):
    image = PIL.Image.open(file_path)

    if show_image:
        image.show()

    image.load()

    return image


def read_image_batch(file_folder_path, file_name_prefix="i", file_name_postfix=".png", page_range=1, show_image=False):
    if type(page_range) == int:
        page_range = np.arange(page_range) + 1
    elif type(page_range) == np.ndarray or type(page_range) == list:
        page_range = page_range
    else:
        print("Invalid range")

    image_list = []

    for r in page_range:
        file_name = "{}{}{}".format(file_name_prefix, r, file_name_postfix)
        file_path = os.path.join(file_folder_path, file_name)
        image_list.append(read_image_file(file_path, show_image=show_image))
        delete_image_file(file_path)

    return image_list


def pre_process_image(image, enhance_factor=0.5, hist_cutoff_pct=2, ignore=None, blur_radius=0.1):
    width, height = image.size

    try:
        if image.mode in ("RGBA", "LA"):
            image_format = image.format
            canvas = PIL.Image.new("RGB", (width, height), (255, 255, 255))
            canvas.paste(image, (0, 0), image)
            image = canvas
            image.format = image_format
    except:
        print("Error removing image transparency\n:{}".format(traceback.format_exc()))

    try:
        if image.mode != "L":
            image = image.convert("L")
    except:
        print("Error converting to greysclae\n:{}".format(traceback.format_exc()))

    try:
        # enhancer = PIL.ImageEnhance.Contrast(image)
        # image = enhancer.enhance(enhance_factor)
        image = PIL.ImageOps.autocontrast(image, cutoff=hist_cutoff_pct, ignore=ignore)
        image = image.filter(PIL.ImageFilter.GaussianBlur(radius=blur_radius))
    except:
        print("Error in enhancing image\n:{}".format(traceback.format_exc()))

    processed_image = image

    return processed_image


def draw_image_box(image, boundbox, color=(255, 0, 0), width=5):
    if type(boundbox) == tuple:
        boundbox = list(boundbox)

    if image.mode == "L" and type(color) == tuple:
        color = 255 - np.average(color)

    draw = PIL.ImageDraw.Draw(image)
    draw.rectangle(xy=boundbox, outline=color, width=width)

    del draw

    return image


def get_active_image_area(image, background="white"):

    image = image.convert("L")

    image = image.filter(PIL.ImageFilter.CONTOUR)

    image = draw_image_box(image, boundbox=[(0, 0), image.size], color=255, width=10)

    image = image.filter(PIL.ImageFilter.MedianFilter(size=3))

    image = image.filter(PIL.ImageFilter.GaussianBlur(radius=25.0))
    image = PIL.ImageOps.autocontrast(image, cutoff=20, ignore=255)
    image = PIL.ImageOps.autocontrast(image, cutoff=20, ignore=0)

    if background == "white":
        background = 255
        canvas = PIL.Image.new(image.mode, image.size, background)
        image_active_area = PIL.ImageChops.subtract(canvas, image)
    elif background == "black":
        background = 0
        canvas = PIL.Image.new(image.mode, image.size, background)
        image_active_area = PIL.ImageChops.subtract(image, canvas)

    boundbox = image_active_area.getbbox()

    return boundbox


def trim_image_border(image, boundbox=None, background="white"):
    if boundbox == None:
        boundbox = get_active_image_area(image, background="white")

    image = image.crop(boundbox)

    return image


def rotate_image(image, resample="NEAREST", angle=0.0):
    if "NEAREST":
        resample = PIL.Image.NEAREST
    elif "BILINEAR":
        resample = PIL.Image.BILINEAR
    elif "BICUBIC":
        resample = PIL.Image.BICUBIC

    rotated_image = image.rotate(angle, resample=resample, expand=1)

    return rotated_image


def orient_image(image, resample="NEAREST"):

    try:
        angle = float(
            image_to_osd(image, lang="eng", oem="3", out="stdout", dpi=70, tessdata_dir=None, os_temp=False)["Rotate"]
        )
    except:
        angle = 0
        print("Error: Orientation Detection Failed!")

    oriented_image = rotate_image(image, resample=resample, angle=angle)
    return oriented_image


def crop_image_region(image, x1=0.0, y1=0.0, x2=1.0, y2=1.0, unit="ratio"):

    width, height = image.size

    if unit == "ratio":
        if x1 <= 1.0 and y1 <= 1.0 and x2 <= 1.0 and y2 <= 1.0:
            box = (int(x1 * width), int(y1 * height), int(x2 * width), int(y2 * height))
            cropped_image = image.crop(box)
        else:
            print("If unit='ratio', 'width' and 'height' both need to be <= 1.0")
            return image
    elif unit == "pixel":
        box = (int(x1), int(y1), int(x2), int(y2))
        cropped_image = image.crop((x1, y1, x2, y2))
    else:
        print("unit not valid")
        return image

    return cropped_image


def write_image_file(image, file_path):
    try:
        image.save(file_path)
    except:
        print("Error in writing file {}\n:{}".format(file_path, traceback.format_exc()))


def write_temp_image_file(image, os_temp=False, temp_folder=None):
    prefix = "tesseract-"
    suffix = ".png"

    if temp_folder == None:
        temp_folder = os.environ["TESSERACT_TEMP"]

    try:
        if os_temp:
            with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False) as f:
                temp_image_file_path = f.name
                image.save(f)
        else:
            temp_image_file_path = os.path.join(temp_folder, "{}{}{}".format(prefix, str(uuid.uuid4()), ".png"))
            write_image_file(image, temp_image_file_path)
    except:
        print("Error in creating temp file: {}\n".format(traceback.format_exc()))

    return temp_image_file_path


def delete_image_file(file_path):
    try:
        os.remove(file_path)
    except:
        print("Error in deleting file {}\n: {}".format(file_path, traceback.format_exc()))


def write_bytes_to_file(file_bytes, file_path=""):
    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except:
        print("Error in writing file: {}\n{}".format(file_path, traceback.format_exc()))


def output_to_lines(output):
    output_lines = output.splitlines()
    return output_lines


def set_tesseract_path(tesseract_path, thread_limit=4, temp_folder=None, tesseract_exe="tesseract.exe"):
    try:
        tesseract_exe = tesseract_exe
        os.environ["TESSERACT_PATH"] = tesseract_path
        os.environ["TESSDATA_PREFIX"] = os.path.join(tesseract_path, "tessdata")
        os.environ["OMP_THREAD_LIMIT"] = str(thread_limit)
        if temp_folder == None:
            temp_folder = os.path.join(tesseract_path, "temp")
        os.environ["TESSERACT_TEMP"] = temp_folder
        os.environ["TESSERACT_APP_COMMAND"] = os.path.join(tesseract_path, tesseract_exe)
    except:
        print("ERROR in setting environment variables:\n{}".format(traceback.format_exc()))


def tesseract_exe(args, decode_output=True):
    output = ""
    error = ""

    command = os.environ["TESSERACT_APP_COMMAND"]
    command_parts = [command] + args
    try:
        p = subprocess.Popen(command_parts, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate(b"input data that is passed to subprocess' stdin")
        if decode_output:
            output = output.decode()
        error = error.decode()
    except:
        print("Error in running tesseract\n{}".format(traceback.format_exc()))
    finally:
        try:
            p.kill()
        except:
            pass

    return output, error


def tesseract(
    image,
    lang="eng",
    psm="3",
    oem="3",
    out="stdout",
    dpi=70,
    config_var=None,
    output_format=None,
    tessdata_dir=None,
    os_temp=False,
    temp_folder=None,
    decode_output=True,
):
    dpi = str(dpi)
    output = ""
    error = ""
    temp_image_file_path = None

    if type(image) == "str":
        try:
            if os.path.isfile(image):
                _, ext = os.path.splitext(image)
                if ext == ".txt":
                    input_type = "list"
                else:
                    input_type = "file"
            else:
                print("ERROR: File path not valid. Check if the file exists")
                return None
        except:
            print("Error in file path provided\n: {}".format(traceback.format_exc()))
    elif type(image).__name__[-9:] == "ImageFile":
        input_type = "image"
        print()
    else:
        return None

    try:
        if input_type == "image":
            temp_image_file_path = write_temp_image_file(image, os_temp=os_temp)
        elif input_type == "list" or input_type == "file":
            temp_image_file_path = image

        if tessdata_dir == None:
            tessdata_dir = os.environ["TESSDATA_PREFIX"]

        args = [temp_image_file_path, out, "--tessdata-dir", tessdata_dir, "--dpi", dpi, "--psm", psm, "--oem", oem]

        if lang != "auto":
            args = args + ["-l", lang]

        if config_var != None:
            args = args + ["-c", config_var]

        if output_format != None:
            args = args + [output_format]

        output, error = tesseract_exe(args, decode_output=decode_output)
        print(error)
    except:
        print("Error in converting image to text\n: {}".format(traceback.format_exc()))
    finally:
        if temp_image_file_path != None:
            delete_image_file(temp_image_file_path)

    if decode_output:
        try:
            output = output[:-1]
        except:
            output = re.sub(r"[\x0c]", "", output)

    gc.collect()
    return output


def get_tesseract_help(option="extra"):
    if option == "extra":
        args = ["--help-extra"]
    elif option == "psm":
        args = ["--help-psm"]
    elif option == "oem":
        args = ["--help-oem"]
    output, error = tesseract_exe(args)

    print(error)

    return output


def get_tesseract_version():
    args = ["--version"]
    output, error = tesseract_exe(args)

    print(error)

    return output


def list_tesseract_languages():
    args = ["--list-langs"]
    output, error = tesseract_exe(args)

    print(error)
    output = output.splitlines()

    return output[1:]


def list_tesseract_parameters():

    args = ["--print-parameters"]
    output, error = tesseract_exe(args)

    print(error)

    return output


def image_to_osd(image, lang="eng", oem="3", out="stdout", dpi=70, tessdata_dir=None, os_temp=False):

    psm = "0"
    output = tesseract(image, lang=lang, psm=psm, oem=oem, out=out, dpi=dpi, tessdata_dir=tessdata_dir, os_temp=os_temp)
    output = output.splitlines()
    osd = {}
    for l in output:
        try:
            field = l.split(":")
            osd.update({field[0]: field[1].strip()})
        except:
            print("Error in splitting field values")

    return osd


def image_to_text(
    image,
    osd=True,
    aps=True,
    sparse=False,
    oem="3",
    lang="eng",
    out="stdout",
    dpi=70,
    tessdata_dir=None,
    os_temp=False,
    return_json=True,
):
    output_format = None

    if osd == True and aps == True:
        psm = "1"
    elif osd == True and sparse == True:
        psm = "12"
    elif sparse == True:
        psm = "11"
    elif aps == True:
        psm = "3"
    else:
        psm = "3"

    output = tesseract(
        image,
        lang=lang,
        psm=psm,
        oem=oem,
        out=out,
        dpi=dpi,
        output_format=output_format,
        tessdata_dir=tessdata_dir,
        os_temp=os_temp,
    )

    if return_json == True:
        text = {"text": output}
    else:
        text = output

    return text


def image_to_text_sparse(image, osd=True, oem="3", lang="eng", out="stdout", dpi=70, tessdata_dir=None, os_temp=False):
    output_format = None

    if osd == True:
        psm = "12"
    else:
        psm = "11"

    output = tesseract(
        image,
        lang=lang,
        psm=psm,
        oem=oem,
        out=out,
        dpi=dpi,
        output_format=output_format,
        tessdata_dir=tessdata_dir,
        os_temp=os_temp,
    )

    text = {"text": output}

    return text


def image_to_text_map(
    image, osd=True, aps=True, oem="3", lang="eng", out="stdout", dpi=70, tessdata_dir=None, os_temp=False
):
    output_format = "tsv"

    if osd == True and aps == True:
        psm = "1"
    elif aps == True:
        psm = "3"

    output = tesseract(
        image,
        lang=lang,
        psm=psm,
        oem=oem,
        out=out,
        dpi=dpi,
        output_format=output_format,
        tessdata_dir=tessdata_dir,
        os_temp=os_temp,
    )

    output = output.splitlines()
    columns = output[0].split("\t")
    data = []
    for row in output[1:]:
        data.append(row.split("\t"))

    text_map = {"columns": columns, "data": data}

    return text_map


def image_to_html(
    image, osd=True, aps=True, oem="3", lang="eng", out="stdout", dpi=70, tessdata_dir=None, os_temp=False
):

    output_format = "hocr"

    if osd == True and aps == True:
        psm = "1"
    elif aps == True:
        psm = "3"

    output = tesseract(
        image,
        lang=lang,
        psm=psm,
        oem=oem,
        out=out,
        dpi=dpi,
        output_format=output_format,
        tessdata_dir=tessdata_dir,
        os_temp=os_temp,
    )

    html = {"html": output}

    return html


def image_to_searchable_pdf(
    image, osd=True, aps=True, sparse=False, oem="3", lang="eng", out="stdout", dpi=70, tessdata_dir=None, os_temp=False
):
    output_format = "pdf"
    if osd == True and aps == True:
        psm = "1"
    elif osd == True and sparse == True:
        psm = "12"
    elif sparse == True:
        psm = "11"
    elif aps == True:
        psm = "3"
    else:
        psm = "3"

    output = tesseract(
        image,
        lang=lang,
        psm=psm,
        oem=oem,
        out=out,
        dpi=dpi,
        output_format=output_format,
        tessdata_dir=tessdata_dir,
        os_temp=os_temp,
        decode_output=False,
    )

    pdf = {"pdf": output}

    return pdf


def create_document_image_table(file_path, start_page=1, end_page=None):
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1][1:].lower()

    if file_extension == "pdf":
        images = pdf_to_images(
            pdf_file=file_path,
            image_format="png",
            dpi=300,
            out_file_prefix="pdf_",
            start_page=start_page,
            end_page=end_page,
            temp_folder=None,
        )
    else:
        images = [read_image_file(file_path=file_path, show_image=False)]

    ImagesTable = pd.DataFrame(data={"Image": images})
    ImagesTable["PageNumber"] = ImagesTable.index + 1
    ImagesTable["FileName"] = file_name

    return ImagesTable


def convert_document_image_table_to_text(
    ImagesTable, osd=True, aps=True, lang="eng", oem="3", dpi=90, tessdata_dir=None, os_temp=False
):
    sparse = False
    out = "stdout"
    return_json = False

    ImagesTable["Text"] = ImagesTable["Image"].apply(
        image_to_text, args=(osd, aps, sparse, oem, lang, out, dpi, tessdata_dir, os_temp, return_json)
    )

    return ImagesTable


def convert_document_file_to_text(
    file_path,
    osd=True,
    aps=True,
    lang="eng",
    dpi=90,
    oem="3",
    start_page=1,
    end_page=None,
    tessdata_dir=None,
    os_temp=False,
):
    ImagesTable = create_document_image_table(file_path, start_page=1, end_page=None)
    ImagesTable = convert_document_image_table_to_text(
        ImagesTable, osd=osd, aps=aps, lang=lang, dpi=dpi, oem=oem, tessdata_dir=tessdata_dir, os_temp=os_temp
    )
    return ImagesTable
