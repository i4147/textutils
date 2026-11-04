from pathlib import Path
from typing import Any

import openpyxl

from .base import BaseGenerator


class XLSXGenerator(BaseGenerator):
    EXTENSIONS = {"xlsx"}

    @classmethod
    def generate(
        cls,
        content: str,
        output_path: Path,
        **kwargs: Any,
    ) -> Path:
        workbook = openpyxl.Workbook()
        try:
            sheet_name = kwargs.get("sheet_name", "Sheet1")
            worksheet = workbook.active
            worksheet.title = sheet_name

            rows = [line.split(",") for line in content.strip().split("\n")]
            for row_idx, row in enumerate(rows, 1):
                for col_idx, value in enumerate(row, 1):
                    worksheet.cell(row=row_idx, column=col_idx, value=value.strip())

            if kwargs.get("auto_adjust", True):
                for column_cells in worksheet.columns:
                    if not column_cells:
                        continue
                    max_length = 0
                    column = column_cells[0].column_letter
                    for cell in column_cells:
                        try:
                            if cell.value and len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            continue
                    if max_length > 0:
                        adjusted_width = (max_length + 2) * 1.2
                        worksheet.column_dimensions[column].width = adjusted_width

            workbook.save(output_path)
            return output_path

        except Exception as e:
            raise IOError(f"Failed to save XLSX file: {e}") from e
        finally:
            try:
                workbook.close()
            except Exception:
                pass

    @classmethod
    def cleanup(cls) -> None:
        pass


def register(registry):
    registry.register(XLSXGenerator())
