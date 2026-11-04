from pathlib import Path
from typing import Any, Optional, Tuple, Type

from ...generators.registration import register_generator_directly


def _get_fpdf() -> Tuple[Optional[Type], Optional[Type], Optional[Type]]:
    try:
        from fpdf import FPDF, XPos, YPos

        return FPDF, XPos, YPos
    except ImportError:
        return None, None, None


def generate_pdf_file(content: str, output_path: Path, **kwargs: Any) -> Path:
    FPDF, XPos, YPos = _get_fpdf()
    if FPDF is None or XPos is None or YPos is None:
        raise ImportError("fpdf2 is required for PDF generation. Install with: pip install fpdf2")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    margin = 25.4
    pdf.set_margins(margin, margin, margin)

    available_width = pdf.w - 2 * margin

    paragraphs = content.split("\n\n")

    for para in paragraphs:
        if not para.strip():
            pdf.ln(10)
            continue

        lines = pdf.multi_cell(w=available_width, h=10, txt=para, split_only=True)

        for line in lines:
            pdf.cell(
                w=available_width,
                h=10,
                txt=line,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

        pdf.ln(5)

    pdf.output(str(output_path))
    return output_path


register_generator_directly(["pdf"], generate_pdf_file)
