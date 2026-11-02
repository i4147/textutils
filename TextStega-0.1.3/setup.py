from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Education",
    "Operating System :: Microsoft :: Windows :: Windows 10",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]
setup(
    name="TextStega",
    version="0.1.3",
    description="A package for Text steganography",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    author="Atharva Vidwans",
    author_email="atharvavidwans@gmail.com",
    license="MIT",
    classifiers=classifiers,
    kerwords="steganography",
    packages=find_packages(),
    install_requires=[""],
)
