import io
import logging
from pathlib import Path
from typing import Any, Optional, Union

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class ExcelGenerator(BaseGenerator):
    @classmethod
    def generate(
        cls,
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        sheet_name = kwargs.get("sheet_name", "Sheet1")
        auto_adjust = kwargs.get("auto_adjust", True)

        output_path = Path(output_path)

        try:
            rows = _parse_csv_content(content)

            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name

            for row_idx, row in enumerate(rows, 1):
                for col_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value.strip())

            if auto_adjust and rows:
                _auto_adjust_columns(ws)

            wb.save(str(output_path))
            logger.debug(f"Generated Excel file: {output_path}")

            return output_path

        except Exception as e:
            if output_path.exists():
                output_path.unlink()
            raise IOError(f"Error generating Excel file: {str(e)}") from e


def _parse_csv_content(content: str) -> list[list[str]]:
    try:
        return [line.split(",") for line in content.strip().split("\n") if line.strip()]
    except Exception as e:
        raise ValueError(f"Failed to parse CSV content: {str(e)}") from e


def _auto_adjust_columns(worksheet: Worksheet) -> None:
    for column_cells in worksheet.columns:
        if not column_cells:
            continue

        max_length = 0
        try:
            column = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    continue

            if max_length > 0:
                adjusted_width = (max_length + 2) * 1.2
                worksheet.column_dimensions[column].width = min(adjusted_width, 50)
        except Exception:
            continue


excel_generator = ExcelGenerator()


def register() -> None:
    from .registration import register_generator

    @register_generator(["xlsx", "xls"])
    def excel_generator_wrapper(
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        return ExcelGenerator.generate(content, output_path, **kwargs)
