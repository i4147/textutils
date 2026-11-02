import contextlib
import inspect
import os
import shutil
import sys

__location__ = os.path.join(os.getcwd(), os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.join(__location__, "../src"))
try:
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc
output_dir = os.path.join(__location__, "api")
module_dir = os.path.join(__location__, "../src/matchtext")
with contextlib.suppress(FileNotFoundError):
    shutil.rmtree(output_dir)
try:
    from pkg_resources import parse_version
    import sphinx

    cmd_line_template = "sphinx-apidoc -f -o {outputdir} {moduledir}"
    cmd_line = cmd_line_template.format(outputdir=output_dir, moduledir=module_dir)
    args = cmd_line.split(" ")
    if parse_version(sphinx.__version__) >= parse_version("1.7"):
        args = args[1:]
    apidoc.main(args)
except Exception as e:
    print("Running `sphinx-apidoc` failed!\n{}".format(e))
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
]
extensions.append("recommonmark")
templates_path = ["_templates"]


def setup(app):
    from recommonmark.transform import AutoStructify

    app.add_config_value(
        "recommonmark_config",
        {"auto_toc_tree_section": "Contents", "enable_eval_rst": True, "enable_math": True, "enable_inline_math": True},
        True,
    )
    app.add_transform(AutoStructify)


source_suffix = [".rst", ".md"]
master_doc = "index"
project = "python-matchtext"
copyright = "2020, Johann Petrak"
version = ""
release = ""
exclude_patterns = ["_build"]
pygments_style = "sphinx"
html_theme = "alabaster"
html_theme_options = {"sidebar_width": "300px", "page_width": "1200px"}
try:
    from matchtext import __version__ as version
except ImportError:
    pass
else:
    release = version
html_static_path = ["_static"]
htmlhelp_basename = "matchtext-doc"
latex_elements = {}
latex_documents = [
    ("index", "user_guide.tex", "python-matchtext Documentation", "Johann Petrak", "manual"),
]
python_version = ".".join(map(str, sys.version_info[0:2]))
intersphinx_mapping = {
    "sphinx": ("http://www.sphinx-doc.org/en/stable", None),
    "python": ("https://docs.python.org/" + python_version, None),
    "matplotlib": ("https://matplotlib.org", None),
    "numpy": ("https://docs.scipy.org/doc/numpy", None),
    "sklearn": ("http://scikit-learn.org/stable", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
}
