# -*- coding: utf-8 -*-

import sys
import os
from recommonmark.parser import CommonMarkParser

# sys.path.insert(0, os.path.abspath('.'))

cwd = os.getcwd()
project_root = os.path.dirname(cwd)

sys.path.insert(0, project_root)

import textar


# needs_sphinx = '1.0'

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

templates_path = ["_templates"]

source_parsers = {
    ".md": CommonMarkParser,
}

source_suffix = [".rst", ".md"]

# source_encoding = 'utf-8-sig'

master_doc = "index"

project = "Analizador de Textos"
copyright = "2016, Datos Argentina"

version = textar.__version__
release = textar.__version__

# language = None

# today = ''
# today_fmt = '%B %d, %Y'

exclude_patterns = ["_build"]

# default_role = None

# add_function_parentheses = True

# add_module_names = True

# show_authors = False

pygments_style = "sphinx"

# modindex_common_prefix = []

# keep_warnings = False


html_theme = "default"

# html_theme_options = {}

# html_theme_path = []

# html_title = None

# html_short_title = None

# html_logo = None

# html_favicon = None

html_static_path = ["_static"]

# html_last_updated_fmt = '%b %d, %Y'

# html_use_smartypants = True

# html_sidebars = {}

# html_additional_pages = {}

# html_domain_indices = True

# html_use_index = True

# html_split_index = False

# html_show_sourcelink = True

# html_show_sphinx = True

# html_show_copyright = True

# html_use_opensearch = ''

# html_file_suffix = None

htmlhelp_basename = "textardoc"


latex_elements = {}

latex_documents = [
    ("index", "textar.tex", "Analizador de Textos Documentation", "Datos Argentina", "manual"),
]

# latex_logo = None

# latex_use_parts = False

# latex_show_pagerefs = False

# latex_show_urls = False

# latex_appendices = []

# latex_domain_indices = True


man_pages = [("index", "textar", "Analizador de Textos Documentation", ["Datos Argentina"], 1)]

# man_show_urls = False


texinfo_documents = [
    (
        "index",
        "textar",
        "Analizador de Textos Documentation",
        "Datos Argentina",
        "textar",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# texinfo_appendices = []

# texinfo_domain_indices = True

# texinfo_show_urls = 'footnote'

# texinfo_no_detailmenu = False
