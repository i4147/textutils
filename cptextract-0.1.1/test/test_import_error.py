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
    def test_corrupted(self):
        extensions = [".ags", ".csv", ".xls", ".xlsx"]
        CPT_import.all_from_folder(folderpath=".\\test\\data\\corruptedfile", accepted_extensions=extensions)
        self.assertEqual(len(CPT_import.all), 3)

        dict3 = consolidate_class_data(auto_delete=True)
        for value in dict3.values():
            value.test_open()

        self.assertEqual(dict3["CPT_114438"].engine, "None")


if __name__ == "__main__":
    unittest.main()
