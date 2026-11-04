import re
import json
from typing import Literal, Optional
import xml.etree.ElementTree as ET
import xmltodict
import html


class StructureExtractor:
    def __init__(self, min_length: int = 10, clean_python_artifacts: bool = True):
        self.min_length = min_length
        self.clean_python_artifacts = clean_python_artifacts

    def extract_xml(self, text: str, return_largest: bool = True) -> str:
        if self.clean_python_artifacts:
            text = self._clean_python_code(text)

        xml_structures = self._find_xml_structures(text)

        if not xml_structures:
            return ""

        if return_largest:
            return self.escape_xml(max(xml_structures, key=len))
        else:
            return self.escape_xml(xml_structures[0])

    def extract_json(self, text: str, return_largest: bool = True) -> str:
        if self.clean_python_artifacts:
            text = self._clean_python_code(text)

        json_structures = self._find_json_structures(text)

        if not json_structures:
            return ""

        if return_largest:
            return max(json_structures, key=len)
        else:
            return json_structures[0]

    def _clean_python_code(self, text: str) -> str:
        text = re.sub(r'^\s*\w+\s*=\s*["\'{]{0,3}', "", text, flags=re.MULTILINE)

        text = re.sub(r'["\'{]{0,3}\s*$', "", text, flags=re.MULTILINE)

        text = re.sub(r'^["\'{]{3,}', "", text)
        text = re.sub(r'["\'{]{3,}$', "", text)

        text = text.strip()

        return text

    def _find_xml_structures(self, text: str) -> list:
        xml_structures = []

        tag_pattern = r"<([a-zA-Z_][a-zA-Z0-9_\-:.]*)\b[^>]*?(?<!/)>"

        for match in re.finditer(tag_pattern, text):
            tag_name = match.group(1)
            start_pos = match.start()

            xml_content = self._extract_balanced_xml(text, start_pos, tag_name)

            if xml_content and len(xml_content) >= self.min_length:
                if self._is_valid_xml_structure(xml_content):
                    xml_structures.append(xml_content.strip())

        seen = set()
        unique_structures = []
        for xml in xml_structures:
            if xml not in seen:
                seen.add(xml)
                unique_structures.append(xml)

        return unique_structures

    def _extract_balanced_xml(self, text: str, start_pos: int, tag_name: str) -> Optional[str]:
        closing_pattern = f"</{tag_name}>"

        search_pos = start_pos
        tag_stack = [tag_name]

        closing_pos = text.find(closing_pattern, start_pos)

        if closing_pos != -1:
            end_pos = closing_pos + len(closing_pattern)
            return text[start_pos:end_pos]

        return None

    def _find_json_structures(self, text: str) -> list:
        json_structures = []

        json_structures.extend(self._find_balanced_structures(text, "{", "}"))

        json_structures.extend(self._find_balanced_structures(text, "[", "]"))

        valid_structures = []
        for structure in json_structures:
            if len(structure) >= self.min_length and self._is_valid_json_structure(structure):
                valid_structures.append(structure.strip())

        seen = set()
        unique_structures = []
        for json_str in valid_structures:
            if json_str not in seen:
                seen.add(json_str)
                unique_structures.append(json_str)

        return unique_structures

    def _find_balanced_structures(self, text: str, start_char: str, end_char: str) -> list:
        structures = []
        i = 0

        while i < len(text):
            if text[i] == start_char:
                balance = 1
                j = i + 1
                in_string = False
                escape_next = False

                while j < len(text) and balance > 0:
                    char = text[j]

                    if escape_next:
                        escape_next = False
                    elif char == "\\" and in_string:
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                    elif not in_string:
                        if char == start_char:
                            balance += 1
                        elif char == end_char:
                            balance -= 1

                    j += 1

                if balance == 0:
                    content = text[i:j]
                    structures.append(content)
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return structures

    def _is_valid_xml_structure(self, text: str) -> bool:
        text = text.strip()

        if not text or not (text.startswith("<") and text.endswith(">")):
            return False

        tag_pattern = r"<[a-zA-Z_][a-zA-Z0-9_\-:.]*(?:\s[^>]*)?>"
        if not re.search(tag_pattern, text):
            return False

        open_tags = len(re.findall(r"<[^/!?][^>]*[^/]>", text))
        close_tags = len(re.findall(r"</[^>]+>", text))
        self_closing = len(re.findall(r"<[^>]+/>", text))

        return abs(open_tags - close_tags) <= 2

    def _is_valid_json_structure(self, text: str) -> bool:
        text = text.strip()

        if not text or not text.startswith(("{", "[")):
            return False

        try:
            json.loads(text)
            return True
        except:
            return self._basic_json_check(text)

    def _basic_json_check(self, text: str) -> bool:
        string_pattern = r'"(?:[^"\\]|\\.)*"'
        cleaned = re.sub(string_pattern, '""', text)

        has_quotes = '"' in text
        has_colons = ":" in cleaned
        has_commas = "," in cleaned
        balanced_braces = cleaned.count("{") == cleaned.count("}")
        balanced_brackets = cleaned.count("[") == cleaned.count("]")

        return balanced_braces and balanced_brackets and has_quotes and (has_colons or has_commas)

    def escape_xml(self, xml_str: str) -> str:

        def escape_element_texts(elem):
            if elem.text:
                elem.text = html.escape(elem.text, quote=False)
            for child in elem:
                escape_element_texts(child)
            if elem.tail:
                elem.tail = html.escape(elem.tail, quote=False)

        xml_str = xml_str.replace("&", "&amp;")
        xml_str = xml_str.replace("<br>", "<br/>")
        xml_str = xml_str.replace("<<", "&lt;&lt;")
        xml_str = xml_str.replace(">>", "&gt;&gt;")

        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError as e:
            print("ParseError:", e)
            raise

        escape_element_texts(root)
        return ET.tostring(root, encoding="unicode")


def clear_llm_res(text: str, extract_strategy: Literal["json", "xml"]) -> str:
    structure_extractor = StructureExtractor()
    if extract_strategy == "json":
        text = structure_extractor.extract_json(text)
    elif extract_strategy == "xml":
        text = structure_extractor.extract_xml(text)
    else:
        raise ValueError(f"Invalid extract_strategy: {extract_strategy}")
    return text.strip()
