# -*- coding: utf-8 -*-

import pathlib
import sys
import traceback

import kglab
import rdflib

from mkrefs import PackageDoc
from mkrefs.util import render_reference


if __name__ == "__main__":
    package_name = "pytextrank"
    git_url = "https://github.com/DerwenAI/pytextrank/blob/main"
    includes = [
        "BaseTextRankFactory",
        "BaseTextRank",
        "PositionRankFactory",
        "PositionRank",
        "BiasedTextRankFactory",
        "BiasedTextRank",
        "Lemma",
        "Paragraph",
        "Phrase",
        "Sentence",
        "VectorElem",
    ]

    pkg_doc = PackageDoc(
        package_name,
        git_url,
        includes,
    )

    try:
        pkg_doc.build()

        groups = {
            "package": [pkg_doc.meta],
        }

        print(groups)

        template_path = pathlib.Path("docs/ref.jinja")
        markdown_path = pathlib.Path("docs/ref.md")

        render_reference(
            template_path,
            markdown_path,
            groups,
        )

        sys.exit(0)

        kg = pkg_doc.get_rdf()
        print(kg.save_rdf_text())

    except Exception:
        traceback.print_exc()
