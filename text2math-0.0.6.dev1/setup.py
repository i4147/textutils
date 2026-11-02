from setuptools import setup, find_packages

with open("README.md") as fp:
    THE_LONG_DESCRIPTION = fp.read()
setup(
    name="text2math",
    url="https://github.com/steven-cutting/text2math",
    version="0.0.6.dev1",
    license="GNU GPL v3+",
    description="Simple package for generating ngrams and bag of words representation from text.",
    long_description=THE_LONG_DESCRIPTION,
    author="Steven Cutting",
    author_email="steven.e.cutting@linux.com",
    classifiers=[
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 2 - Pre-Alpha",
    ],
    keywords="nlp text ngram ngrams",
    packages=find_packages(exclude=("bin", "tests", "docker", "data", "notebooks")),
    install_requires=[
        "toolz>=0.7.4",
        "chardet>=2.3.0",
        "unidecode>=0.04.19",
        "ftfy>=4.0.0",
    ],
    extras_require={
        "faster": ["cchardet>=1.0.0", "cytoolz>=0.7.3"],
        "extra": ["beautifulsoup4>=4.4.0", "lxml>=3.4.4"],
        "dev": ["cchardet>=1.0.0", "cytoolz>=0.7.3", "beautifulsoup4>=4.4.0", "lxml>=3.4.4"],
        "test": ["pytest-runner>=2.6.2", "pytest>=2.8.7"],
    },
    setup_requires=["pytest-runner>=2.6.2"],
    tests_require=["pytest>=2.8.7"],
    package_data={
        "": [
            "*.json",
        ],
    },
)
