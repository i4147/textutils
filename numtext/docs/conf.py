#
#
#
#

#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import numtext


#
# needs_sphinx = '1.0'

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

templates_path = ["_templates"]

#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

master_doc = "index"

project = "numtext"
copyright = "2022, Sumanth"
author = "Sumanth"

#
version = numtext.__version__
release = numtext.__version__

#
language = None

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = "sphinx"

todo_include_todos = False


#
html_theme = "alabaster"

#
# html_theme_options = {}

html_static_path = ["_static"]


htmlhelp_basename = "numtextdoc"


latex_elements = {
    #
    #
    #
    #
}

latex_documents = [
    (master_doc, "numtext.tex", "numtext Documentation", "Sumanth", "manual"),
]


man_pages = [(master_doc, "numtext", "numtext Documentation", [author], 1)]


texinfo_documents = [
    (
        master_doc,
        "numtext",
        "numtext Documentation",
        author,
        "numtext",
        "One line description of project.",
        "Miscellaneous",
    ),
]
