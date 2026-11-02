from setuptools import find_packages, setup

classifiers = [
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing",
    "Topic :: Text Processing :: General",
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: Legal Industry",
    "Intended Audience :: Science/Research",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]
LD = open("README.md").read()
setup(
    name="keytext",
    version="0.3",
    description="Keyword based text extraction Pacakage (keytext)",
    long_description=LD,
    long_description_content_type="text/markdown",
    url="",
    author="Soumyajit Basak",
    author_email="soumyabasak96@gmail.com",
    License="MIT",
    classifiers=classifiers,
    keywords=["textmining", "NLP", "document intelligence"],
    packages=find_packages(),
    install_requires=["regex", "pandas"],
)
