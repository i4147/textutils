from pdf2image import convert_from_path
import pytesseract
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLineHorizontal
from pathlib import Path
from enum import Enum
import shutil

PDF_MAGIC_HEADER = b"%PDF-"


class FileType(str, Enum):
    PDF = "PDF"
    TEXT = "Plain Text"
    UNSUPPORTED = "Unsupported"


class File:
    def __init__(
        self,
        filetype: FileType = None,
        text: str = None,
        pages: list[str] = None,
    ) -> None:
        self.filetype = filetype
        self.text = text
        self.pages = pages


class Textifier:
    supported_filetypes = [FileType.PDF, FileType.TEXT]

    def __init__(self, log=print, progress_fn=None):
        self.log = log
        self.progress_fn = progress_fn

    def filetype(self, file: Path) -> FileType:
        try:
            with open(file, "rb") as f:
                header = f.read(5)
                if header == PDF_MAGIC_HEADER:
                    return FileType.PDF
            with open(file, "r", encoding="utf-8") as f:
                f.read(1)
                return FileType.TEXT
        except UnicodeDecodeError:
            return FileType.UNSUPPORTED

    def extract_text(
        self,
        file: Path,
        use_ocr: bool = False,
    ) -> File:
        filetype = self.filetype(file)
        text = None
        pages = None
        if not filetype in self.supported_filetypes:
            self.log("Unsupported filetype.")
        elif filetype == FileType.TEXT:
            text = self.text_from_text(file).strip()
        elif filetype == FileType.PDF:
            if use_ocr:
                try:
                    pages = self.text_from_pdf_ocr(file)
                except Exception as e:
                    self.courtesy_check_ocr_dependencies()
                    raise e
            else:
                pages = self.text_from_pdf_extraction(file)
        return File(filetype=filetype, text=text, pages=pages)

    def text_from_text(self, file: Path) -> str:
        with open(file, "r", encoding="utf-8") as f:
            return f.read()

    def text_from_pdf_ocr(self, file: Path) -> list[str]:
        self.log("Starting PDF conversion for OCR...")
        pages = convert_from_path(file)
        self.log("Conversion complete.\nStarting OCR...")
        total = len(pages)
        texts = []
        for idx, page in enumerate(pages):
            if self.progress_fn:
                self.progress_fn(f"\rConverting page {idx + 1}/{total}")
                if idx + 1 == total:
                    self.progress_fn("\n")
            texts.append(pytesseract.image_to_string(page))
        return texts

    def text_from_pdf_extraction(self, file: Path) -> list[str]:
        pages = []
        self.log("Starting extraction...")
        for page_layout in extract_pages(file):
            page_lines = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if isinstance(text_line, LTTextLineHorizontal):
                            page_lines.append((text_line.y0, text_line.get_text()))
            page_lines.sort(reverse=True, key=lambda x: x[0])
            pages.append("".join([text for _, text in page_lines]))

        self.log("Extraction complete.")
        return pages

    def courtesy_check_ocr_dependencies(self) -> None:
        tesseract = shutil.which("tesseract")
        poppler = shutil.which("pdftoppm")
        if not poppler:
            poppler = shutil.which("pdftocairo")
        if poppler and tesseract:
            return

        missing = ["tesseract" if not tesseract else None, "poppler" if not poppler else None]
        missing = (", ").join(missing)
        self.log(
            f"Tesseract and Poppler must both be installed on your system to use OCR. It looks like you may be missing [{missing}]."
        )
