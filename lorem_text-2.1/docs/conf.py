import os
import sys

sys.path.insert(0, os.path.abspath(".."))
import lorem_text

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "Lorem Text"
copyright = "2021, Abhijeet Pal"
author = "Abhijeet Pal"
version = lorem_text.__version__
release = lorem_text.__version__
language = None
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
htmlhelp_basename = "lorem_textdoc"
latex_elements = {}
latex_documents = [
    (master_doc, "lorem_text.tex", "Lorem Text Documentation", "Abhijeet Pal", "manual"),
]
man_pages = [(master_doc, "lorem_text", "Lorem Text Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        "lorem_text",
        "Lorem Text Documentation",
        author,
        "lorem_text",
        "One line description of project.",
        "Miscellaneous",
    ),
]
