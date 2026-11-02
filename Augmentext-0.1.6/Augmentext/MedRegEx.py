import re

cm = re.compile("[+-]?(\d*\.)?\d+\s*(cm|centimeters|centimetres)(.|\W|-)")
mm = re.compile("[+-]?(\d*\.)?\d+\s*mm")
mg_dl = re.compile("[+-]?(\d*\.)?\d+\s*mg/dl")
mg_dl = re.compile("[+-]?(\d*\.)?\d+\s*(g|grams)/l")
kg_m2 = re.compile("[+-]?(\d*\.)?\d+\s*(kgm2|kg m2)(.|\W|-)")
centigrade = re.compile("[+-]?(\d*\.)?\d+\s*C")
centigrade_variants = ["C", "°C", "centigrade"]
mm_hg = re.compile("[+-]?(\d*\.)?\d+\s*(mmHg|mm Hg|mm/Hg)(.|\W|-)")
mm_hg_variants = ["mmHg", "mm Hg", "mm/Hg"]
text_text = """
Blood pressure of 34.2 mm Hg.
Blood pressure of 34.2 mmHg.
Blood pressure of 34.2mmHg.
Fat body was 30.1 kg/m2.
Incision was 34.4cm.
Incision was 1.1in.
Incisoin was 1.1 in.
Incision was 1.1 inches.
"""
