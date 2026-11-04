import os
import sys
import shutil


__location__ = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(__location__, "../src"))


try:
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc

output_dir = os.path.join(__location__, "api")
module_dir = os.path.join(__location__, "../src/texted")
try:
    shutil.rmtree(output_dir)
except FileNotFoundError:
    pass

try:
    import sphinx

    cmd_line = f"sphinx-apidoc --implicit-namespaces -f -o {output_dir} {module_dir}"

    args = cmd_line.split(" ")
    if tuple(sphinx.__version__.split(".")) >= ("1", "7"):
        args = args[1:]

    apidoc.main(args)
except Exception as e:
    print("Running `sphinx-apidoc` failed!\n{}".format(e))


# needs_sphinx = '1.0'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.extlinks",
    "sphinx_copybutton",
    "sphinxemoji.sphinxemoji",
]

templates_path = ["_templates"]

source_suffix = ".rst"

# source_encoding = 'utf-8-sig'

master_doc = "index"

project = "texted"
copyright = "2023, Anderson Bravalheri"
repository = "https://github.com/pyscaffold/texted/"

try:
    from texted import __version__ as version
except ImportError:
    version = ""

if not version or version.lower() == "unknown":
    version = os.getenv("READTHEDOCS_VERSION", "unknown")

release = version

# language = None

# today = ''
# today_fmt = '%B %d, %Y'

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv"]

# default_role = None

# add_function_parentheses = True

# add_module_names = True

# show_authors = False

pygments_style = "sphinx"

# modindex_common_prefix = []

# keep_warnings = False

todo_emit_warnings = True


html_theme = "furo"

html_theme_options = {
    "navigation_with_keys": True,
}

# html_theme_path = []

# html_title = None

# html_short_title = None

# html_logo = ""

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

htmlhelp_basename = "texted-doc"


latex_elements = {}

latex_documents = [("index", "user_guide.tex", "texted Documentation", "Anderson Bravalheri", "manual")]

# latex_logo = ""

# latex_use_parts = False

# latex_show_pagerefs = False

# latex_show_urls = False

# latex_appendices = []

# latex_domain_indices = True

python_version = ".".join(map(str, sys.version_info[0:2]))
intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "python": ("https://docs.python.org/" + python_version, None),
    "matplotlib": ("https://matplotlib.org", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "setuptools": ("https://setuptools.pypa.io/en/stable/", None),
    "pyscaffold": ("https://pyscaffold.org/en/stable", None),
}
extlinks = {
    "issue": (f"{repository}/issues/%s", "issue #%s"),
    "pr": (f"{repository}/pull/%s", "PR #%s"),
    "discussion": (f"{repository}/discussions/%s", "discussion #%s"),
    "pypi": ("https://pypi.org/project/%s", "%s"),
    "github": ("https://github.com/%s", "%s"),
}

print(f"loading configurations for {project} {version} ...", file=sys.stderr)
