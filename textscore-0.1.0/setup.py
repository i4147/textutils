from setuptools import setup

packages = ["textscore"]
package_data = {"": ["*"]}
install_requires = ["torch>=1.13.1,<2.0.0", "transformers>=4.25.1,<5.0.0"]
setup_kwargs = {
    "name": "textscore",
    "version": "0.1.0",
    "description": "Tool for assesing the quality of text using causal LM.",
    "long_description": "# TextScore\n",
    "author": "Alex Varga",
    "author_email": "alex@hylix.co",
    "maintainer": "None",
    "maintainer_email": "None",
    "url": "None",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.10,<4.0",
}
setup(**setup_kwargs)
