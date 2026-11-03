import os
from dotenv import load_dotenv
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

load_dotenv()


def preprocess_image(image: Image.Image) -> Image.Image:
    if image.mode != "L":
        image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    threshold = 150
    image = image.point(lambda p: 255 if p > threshold else 0)
    return image


def image_to_text(image_path: str) -> str:
    print(f"[OCR] Starting OCR for {image_path}")
    try:
        tesseract_path = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"[OCR] Using tesseract at: {tesseract_path}")
        image = Image.open(image_path)
        processed = preprocess_image(image)
        config = r"--oem 1 --psm 6"
        text: str = pytesseract.image_to_string(processed, config=config, lang="eng")
        print(f"[OCR] Extracted text for {image_path}:\n{text}\n---")
        return text
    except Exception as e:
        print(f"[OCR] Error processing {image_path}: {e}")
        return ""
