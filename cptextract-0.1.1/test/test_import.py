# test directory is not in the same folder as package
# make local package dicoverable to test
import sys
import os

print(os.getcwd())
# print(sys.path)
sys.path.append(os.getcwd())

# unit testing
import unittest

# from unittest.mock import patch
from cptextract.check_files import *


class TestImportFunctions(unittest.TestCase):
    def test_import(self):
        extensions = [".ags", ".csv", ".xls", ".xlsx"]
        CPT_import.all_from_folder(folderpath=".\\test\\data\\typical nzgd", accepted_extensions=extensions)
        self.assertEqual(len(CPT_import.all), 36)

        dict3 = consolidate_class_data(auto_delete=True)
        self.assertEqual(len(dict3.keys()), 24)

        self.assertEqual(len(CPT_import.all), 24)

    def test_non_numeric(self):
        cpt1 = CPT_import(".\\test\\data\\CPT_140951_Raw01.CSV")
        cpt1.auto_extract()
        self.assertEqual(cpt1.okay_calc, False)
        self.assertEqual(cpt1.error_msg, "CPT_140951.csv non-numeric data present!; ")


if __name__ == "__main__":
    unittest.main(buffer=True)
