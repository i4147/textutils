import os
import fitz
from PIL import Image


def pdf_to_images(pdf_path: str, output_folder: str) -> None:
    os.makedirs(output_folder, exist_ok=True)
    pdf_document = fitz.open(pdf_path)
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        pixmap = page.get_pixmap()
        mode = "RGB" if pixmap.n < 5 else "CMYK"
        image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
        image_path = os.path.join(output_folder, f"page_{page_number + 1}.png")
        image.save(image_path)
        print(f"Page {page_number + 1} converted and saved as {image_path}")
    pdf_document.close()
