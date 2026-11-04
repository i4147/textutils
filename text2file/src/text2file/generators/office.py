import io
import sys
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

GeneratorFunc = TypeVar("GeneratorFunc", bound=Callable[..., Optional[Path]])

register_generator = None


def _register_generators():
    if register_generator is not None:
        register_generator(["docx"])(generate_docx_file)
        register_generator(["xlsx"])(generate_xlsx_file)
        register_generator(["odt"])(generate_odt_file)


def _on_import():
    if register_generator is not None:
        _register_generators()


import atexit

atexit.register(_on_import)


def _get_docx():
    try:
        from docx import Document

        return Document
    except ImportError:
        return None


def _get_openpyxl():
    try:
        from openpyxl import Workbook

        return Workbook
    except ImportError:
        return None


def generate_docx_file(content: str, output_path: Path) -> Optional[Path]:
    Document = _get_docx()
    if Document is None:
        raise ImportError("python-docx is required for DOCX generation. Install with: pip install python-docx")

    doc = Document()
    doc.add_paragraph(content)
    doc.save(str(output_path))
    return output_path


def generate_xlsx_file(content: str, output_path: Path) -> Optional[Path]:
    Workbook = _get_openpyxl()
    if Workbook is None:
        raise ImportError("openpyxl is required for XLSX generation. Install with: pip install openpyxl")

    wb = Workbook()
    ws = wb.active

    rows = [line.split("\t") for line in content.split("\n") if line.strip()]

    for row_idx, row in enumerate(rows, 1):
        for col_idx, cell_value in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value)

    wb.save(str(output_path))
    return output_path


def generate_odt_file(content: str, output_path: Path) -> Optional[Path]:
    try:
        from odf import opendocument, style, text
    except ImportError:
        raise ImportError("python-odf is required for ODT generation. Install with: pip install python-odf")

    doc = opendocument.OpenDocumentText()

    s = doc.styles

    para_style = style.Style(name="Standard", family="paragraph")
    para_style.addElement(style.TextProperties(fontfamily="Arial", fontsize="12pt"))
    doc.automaticstyles.addElement(para_style)

    for line in content.split("\n"):
        p = text.P(stylename=para_style, text=line)
        doc.text.addElement(p)

    doc.save(str(output_path), True)
    return output_path
