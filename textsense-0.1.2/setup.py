from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="textsense",
    version="0.1.2",
    description="TextSense.ai a Text analytics platform.",
    author="TextSense Team",
    author_email="agambhire@algoanalytics.com",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "requests",
    ],
    packages=["textsense"],
    zip_safe=False,
)
