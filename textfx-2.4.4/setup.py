from pathlib import Path
from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name="textfx",
    version="2.4.4",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=["termcolor"],
    description="textfx is a Python library for creating dynamic and visually engaging text effects and Loading Animation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ilia Karimi",
    author_email="iliakarimi.dev@gmail.com",
    license="MIT",
    url="https://github.com/iliakarimi/textfx",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
