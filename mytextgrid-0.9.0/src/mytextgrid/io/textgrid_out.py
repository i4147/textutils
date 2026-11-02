import csv
from decimal import Decimal
import json
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


def textgrid_to_text_file(textgrid_obj, dst_path, short_format=False, encoding="utf-8"):
    env = Environment(loader=PackageLoader("mytextgrid.io"), autoescape=select_autoescape())
    env.trim_blocks = True
    env.lstrip_blocks = True
    dict_ = textgrid_obj.to_dict()
    template_name = "short_format.TextGrid.jinja" if short_format else "long_format.TextGrid.jinja"
    template = env.get_template(template_name)
    textgrid_str = template.render(textgrid=dict_)
    with open(dst_path, "w", encoding=encoding) as textfile:
        textfile.write(textgrid_str)


def to_csv(textgrid_obj, path, encoding="utf-8"):
    table = []
    for tier in textgrid_obj:
        for item in tier:
            if item.text == "":
                continue
            if tier.is_interval():
                table.append([item.xmin, tier.name, item.text, item.xmax])
            else:
                table.append([item.time, tier.name, item.text, item.time])
    table.sort(key=lambda x: x[0])
    with open(path, "w", encoding=encoding, newline="") as file_object:
        spamwriter = csv.writer(file_object)
        spamwriter.writerow(["tmin", "tier_name", "text", "tmax"])
        for row in table:
            spamwriter.writerow([str(item) for item in row])


def textgrid_to_json(textgrid_obj, path, encoding="utf-8"):
    dict_ = textgrid_obj.to_dict()
    with open(path, "w", encoding=encoding) as file_object:
        json.dump(dict_, file_object, cls=_DecimalEncoder, ensure_ascii=False, indent=4)


class _DecimalEncoder(json.JSONEncoder):
    def default(self, decimal_number):
        if isinstance(decimal_number, Decimal):
            return str(decimal_number)
        else:
            return super().default(decimal_number)
