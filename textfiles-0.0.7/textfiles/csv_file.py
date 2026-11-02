from .text_file_parent import TextFile
import csv, os
from .exceptions import *


class CsvFile(TextFile):
    def __init__(self, file_path, delimiter=",", has_header=True, as_dict=False):
        self._isheader = has_header
        self._delimiter = delimiter
        self.as_dict = as_dict
        super().__init__(file_path)
        self.connection = ""

    def __str__(self):
        return (
            f"{self.file_name}\n"
            f"contains {len(self)} rows\n"
            f"header: {self.header}\n"
            f"file creation time: {self.creation_time}\n"
            f"file last modified: {self.last_modified}"
        )

    def __contains__(self, item):
        for row in self._content:
            if item in row:
                return True
        return False

    def __add__(self, other: CsvFile):
        if not isinstance(other, CsvFile):
            raise InstanceError(type(other), "csv")
        h1 = self.header
        h2 = other.header
        if None in (h1, h2):
            raise HeaderError("Both files should be with header")
        if not self._is_identical(h1, h2):
            raise HeaderError("The headers are not identical")
        new_fp = os.path.join(self.root, self.file_name + "_" + other.file_name + self._ext)
        if os.path.exists(new_fp):
            raise PathAlreadyExistsError(new_fp)
        with open(new_fp, "w", newline="") as new_csv:
            writer = csv.writer(new_csv)
            for row in self.content:
                writer.writerow(row)
            for row in other.content[1:]:
                writer.writerow(row)
        new_csv = CsvFile(new_fp, has_header=True)
        return new_csv

    def __len__(self):
        if self._isheader:
            num_of_rows = -1
        else:
            num_of_rows = 0
        for row in self._content:
            print(row)
            print(num_of_rows)
            num_of_rows += 1
        return num_of_rows

    def __iter__(self):
        for row in self.content():
            yield row

    def shape(self):
        num_of_rows = 0
        for row in self._content:
            num_of_rows += 1
        num_of_col = len(self.content[0])
        return num_of_rows, num_of_col

    @property
    def header(self) -> list | None:
        if self._isheader:
            return self.content[0]
        else:
            return None

    def get_row(self, n, w=False):
        if n not in range(len(self)):
            raise OutOfRange(n)
        wanted_row = self.content[n]
        if w:
            if self._isheader:
                wanted_row = {wanted_row[i]: self.header[i] for i in range(len(wanted_row))}
            else:
                raise HeaderError("File has no header")
            return wanted_row

    def get_column_header(self, n):
        if self._isheader:
            return self.header[n]
        else:
            return None

    def get_column_data(self, n):
        column_data = [self.content[n] for row in self.content]
        return column_data

    def get_cell(self, row_num, column_num):
        with open(self._file_path, "r", newline="") as csvf:
            read_f = csv.reader(csvf, delimiter=self._delimiter)
            csv_list = list(read_f)
            if len(csv_list) < row_num - 1 and len(csv_list[0]) < column_num:
                pass
            return csv_list[row_num][column_num - 1]

    def search(self, value):
        locations = []
        for index, row in enumerate(self._content):
            if value in row:
                for i, v in enumerate(row):
                    if v == value:
                        locations.append((index, i))
        return locations

    def count(self, value) -> int:
        return len(self.search(value))

    def add_row(self, row_to_add: list):
        self.lock.acquire()
        with open(self.file_path, "a") as f:
            writer = csv.writer(f, delimiter=self._delimiter)
            writer.writerow(row_to_add)
        self.lock.release()

    def delete_row(self, row_num=None, row_content=None):
        self.lock.acquire()
        content = self.content
        if row_num:
            row_content = content[row_num]
        content.remove(row_content)
        with open(self.file_path, "w") as fh:
            writer = csv.writer(fh)
            writer.writerows(content)
        self.lock.release()

    def update_cell(self, cell_row, cell_column, new_value):
        if cell_row > len(self):
            raise OutOfRange(cell_row)
        if cell_column > len(self.content[1]):
            raise OutOfRange(cell_column)
        self.lock.acquire()
        content = self.content()
        content[cell_row][cell_column] = new_value
        with open(self.file_path, "w") as fh:
            writer = csv.writer(fh)
            writer.writerows(content)
        self.lock.release()

    def average(self, n, beginning_row=0, end_row=None):
        sum_num = self.sum_column(n, beginning_row, end_row if end_row is not None else len(self))
        divider = len(self.content[beginning_row : end_row if end_row is not None else len(self)])
        return sum_num / divider

    def sum_column(self, n, beginning_row=0, end_row=None):
        sum_num = 0
        column = self.get_column_data(n)
        for item in column[beginning_row : end_row if end_row is not None else len(self)]:
            if isinstance(item, (int, float)):
                sum_num += item
        return sum_num

    def _csv_list(self, fd):
        ret_val = []
        for row in csv.reader(fd, delimiter=self._delimiter):
            ret_val.append(row)
        return ret_val

    def _csv_dict(self, fd):
        ret_val = []
        for row in csv.DictReader(fd, delimiter=self._delimiter):
            ret_val.append(row)
        return ret_val

    def _specific_content(self, fd):
        if not self.as_dict:
            return self._csv_list(fd)
        return self._csv_dict(fd)

    def _ext(self):
        return "csv"

    @staticmethod
    def _is_identical(h1: list, h2: list) -> bool:
        return h1 == h2
