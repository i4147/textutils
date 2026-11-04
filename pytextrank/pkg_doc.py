# -*- coding: utf-8 -*-


import importlib
import json
import sys

import pyfixdoc


if __name__ == "__main__":
    ref_md_file: str = sys.argv[1]

    sys.path.insert(0, "../")

    with open("pkg_doc.cfg", "r", encoding="utf-8") as fp:
        config: dict = json.load(fp)

        importlib.import_module(config["module"])

        pkg_doc: pyfixdoc.PackageDoc = pyfixdoc.PackageDoc(
            config["module"],
            config["src_url"],
            config["classes"],
        )

        # pkg_doc.show_all_elements(); sys.exit(0)

        pkg_doc.build()

        pkg_doc.write_markdown(ref_md_file)
