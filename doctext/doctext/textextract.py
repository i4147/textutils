import tempfile, os, logging
from pathlib import Path
from tika import parser
from PIL import Image
import pytesseract
from termcolor import cprint
import magic
from openai import OpenAI
import chardet
from langdetect import detect
from iso639 import Lang
from doctext.utils import run_checked, log_exception
from doctext.Capabilities import Capabilities
import pdfminer.high_level
from docling.document_converter import DocumentConverter

log = logging.getLogger("doctext.textextract")


def is_plain_text(mimetype: str) -> bool:
    if mimetype and mimetype.startswith("text/"):
        return True
    if mimetype and "/json" in mimetype:
        return True
    if mimetype and "/yaml" in mimetype:
        return True
    if mimetype and "/xml" in mimetype:
        return True
    if mimetype and "/csv" in mimetype:
        return True
    if mimetype and "/markdown" in mimetype:
        return True
    if mimetype and "/html" in mimetype:
        return True
    if mimetype and "/xhtml" in mimetype:
        return True
    return False


def extract_pdf(file_path: str, tesseract_lang: str = None) -> str | None:

    text = ""

    try:
        log.info(f"Extracting text from '{file_path}' using pdfminer")
        text = pdfminer.high_level.extract_text(file_path)
        text = text.strip()
        if len(text) > 0:
            return text
    except Exception as e:
        log_exception(log, e, f"Failed to extract text from '{file_path}' using pdfminer")

    try:
        log.info(f"Extracting text from '{file_path}' using pdftotext")
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpf = os.path.join(tmpdirname, "text.txt")
            if run_checked(["pdftotext", "-enc", "UTF-8", file_path, tmpf]):
                with open(tmpf, "r") as file:
                    text = file.read()
                    text = text.strip()
            if len(text) > 0:
                return text
    except Exception as e:
        log_exception(log, e, f"Failed to extract text from '{file_path}' using pdftotext")

    return ocr_pdf(file_path, tesseract_lang)


def do_ocr_pdf(file_path: str, tesseract_lang: str) -> str | None:
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpf = os.path.join(tmpdirname, "ocred.pdf")
            cmd = ["ocrmypdf", "-l", tesseract_lang, "--redo-ocr", "-c", "--sidecar", "-", file_path, tmpf]
            code, stdout, _ = run_checked(cmd, return_output=True)
            if code:
                return stdout
    except Exception as e:
        log_exception(log, e, f"Failed to OCR {file_path}")

    return None


def ocr_pdf(file_path: str, tesseract_lang: str = None) -> str | None:

    log.info(f"Extracting text from '{file_path}' using ocrmypdf")

    _lang = "eng"
    if tesseract_lang is not None:
        _lang = tesseract_lang

    text = do_ocr_pdf(file_path, _lang)

    if text is not None:
        lang = Lang(detect(text)).pt3
        if lang != _lang:
            log.info(f"Detected language '{lang}' but ran OCR with language '{_lang}'. Redoing OCR.")
            text = do_ocr_pdf(file_path, lang)

    return text


def extract_plain_text(file_path: str) -> str | None:

    log.info(f"Extracting plain text from '{file_path}'")

    try:
        with open(file_path, "rb") as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]

        with open(file_path, "r", encoding=encoding) as file:
            content = file.read()

        return content.encode("utf-8")
    except Exception as e:
        log_exception(log, e, f"Failed to extract plain text from '{file_path}'")

    return None


def convert_to_string_if_bytes(text):
    if isinstance(text, bytes):
        detected_encoding = chardet.detect(text)["encoding"]
        if detected_encoding:
            return text.decode(detected_encoding)
        else:
            log.warning("Unable to detect encoding for byte conversion. Using UTF-8.")
            return text.decode("utf-8")
    else:
        return text


def extract_text_postprocess(func):

    def wrapper(*args, **kwargs):
        text = func(*args, **kwargs)
        text = convert_to_string_if_bytes(text)
        if text:
            return text.replace("\x00", "")
        return text

    return wrapper


def ocr(image_path, tesseract_lang: str = None):

    log.info(f"Running OCR with pytesseract on '{image_path}'")

    _lang = "eng"
    if tesseract_lang is not None:
        _lang = tesseract_lang

    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=_lang)

        try:
            lang = Lang(detect(text)).pt3
            if lang != _lang:
                log.info(f"Ran OCR with language '{_lang}' but detected language '{lang}'. Redoing OCR.")
                return pytesseract.image_to_string(img, lang=lang)
        except Exception as e:
            log_exception(log, e, f"Failed to OCR {image_path}")

        return text

    except Exception as e:
        log_exception(log, e, f"Failed to OCR {image_path}")

    return None


def extract_text_from_image(image_path: str, tesseract_lang: str = None) -> str | None:

    def heic_to_png(src: str, dest: str) -> bool:
        if run_checked(["heif-convert", src, dest]):
            return os.path.exists(dest)
        return False

    def cr2_to_png(src: str, dest: str) -> bool:
        if run_checked(["dcraw", "-c", "-w", src, "|", "pnmtopng", ">", dest]):
            return os.path.exists(dest)
        return False

    def any_to_png_pil(src: str, dest: str) -> bool:
        try:
            with Image.open(src) as img:
                img.save(dest, "PNG")
                return os.path.exists(dest)
        except Exception as e:
            log_exception(log, e, f"Failed to convert image {image_path} with PIL.")
        return False

    def any_to_png_im(src: str, dest: str) -> bool:
        if run_checked(["convert", src, dest]):
            return os.path.exists(dest)
        return False

    def any_to_png_ffmpeg(src: str, dest: str) -> bool:
        if run_checked(["ffmpeg", "-i", src, "-vf", "scale=1920:-1", dest]):
            return os.path.exists(dest)
        return False

    def to_png(src: str, dest: str) -> bool:
        if any_to_png_pil(src, dest):
            return True
        elif any_to_png_im(src, dest):
            return True
        elif any_to_png_ffmpeg(src, dest):
            return True
        elif heic_to_png(src, dest):
            return True
        elif cr2_to_png(src, dest):
            return True
        else:
            return False

    mime = magic.Magic(mime=True)
    mimetype = mime.from_file(image_path)

    if mimetype not in ["image/jpeg", "image/png", "image/jpg"] or Path(image_path).suffix == ".jpe":
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpimg = os.path.join(tmpdirname, "image.png")
            if to_png(image_path, tmpimg):
                return ocr(tmpimg, tesseract_lang)
            else:
                log.warning(f"Cannot convert '{image_path}' to PNG")
                return None

    return ocr(image_path, tesseract_lang)


def extract_text_from_video(f: Path) -> str:

    log.info(f"Extracting text from '{f}' using ffmpeg")

    text = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        if run_checked(["ffmpeg", "-i", str(f), f"{tmpdirname}/image%d.jpg"]):
            images = sorted(
                os.path.abspath(os.path.join(tmpdirname, f)) for f in os.listdir(tmpdirname) if f.endswith(".jpg")
            )
            for image in images:
                try:
                    text.append(ocr(image))
                except Exception as ex:
                    log.warning(f"Cannot extract text from {image}\n{ex}")
        return " ".join(text)


def extract_text_from_audio(f: Path, openai_api_key: str) -> str | None:

    log.info(f"Extracting text from '{f}' using OpenAI")

    if openai_api_key is None:
        log.warning("No OpenAI API key provided. Skipping audio to text conversion.")
        return None

    client = OpenAI(api_key=str(openai_api_key))
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpf = os.path.join(tmpdirname, "audio.m4a")
            if run_checked(["ffmpeg", "-i", str(f), "-c:a", "aac", "-b:a", "192k", tmpf]):
                return client.audio.transcriptions.create(
                    model="whisper-1", file=open(tmpf, "rb"), response_format="text"
                )
    except Exception as e:
        log_exception(log, e, f"Cannot extract text from {str(f)}\n{ex}")
    return None


def tika(file_path):

    log.info(f"Extracting text from '{file_path}' using tika")

    try:
        parsed = parser.from_file(file_path)
        return parsed["content"]
    except Exception as e:
        log_exception(log, e, f"Failed to extract text with tika from {file_path}")
    return None


@extract_text_postprocess
def extract_text(
    file_path: str, openai_api_key: str = None, tesseract_lang: str = None, capabilities: Capabilities = None
) -> str | None:

    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        return result.document.export_to_markdown()
    except Exception as e:
        log_exception(log, e, f"Failed to extract text from '{file_path}' using docling")

    mime = magic.Magic(mime=True)
    mimetype = mime.from_file(file_path)

    if is_plain_text(mimetype):
        return extract_plain_text(file_path)
    if mimetype and mimetype.startswith("image/"):
        return extract_text_from_image(file_path, tesseract_lang)
    if mimetype and mimetype.startswith("video/"):
        # return extract_text_from_video(file_path)
        return extract_text_from_audio(file_path, openai_api_key)
    if mimetype and mimetype.startswith("audio/"):
        return extract_text_from_audio(file_path, openai_api_key)
    if mimetype and mimetype.startswith("application/pdf"):
        return extract_pdf(file_path, tesseract_lang)

    return tika(file_path)
