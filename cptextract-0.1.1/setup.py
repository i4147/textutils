from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()
setup(
    name="cptextract",
    description="A simple Python package to automate the extraction of CPT data",
    version="0.1.1",
    packages=find_packages(),
    long_description=description,
    long_description_content_type="text/markdown",
    author="geocoder-eng",
    url="https://github.com/geocodes-eng/cptextract",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="geotechnical, cpt",
    install_requires=[
        "numpy",
        "pandas",
        "python-ags4",
        "openpyxl",
        "xlrd",
        "pyexcel",
    ],
)
