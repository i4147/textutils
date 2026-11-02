from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="MarkovText",
    version="0.1dev7",
    description="A package to generate text via Markov chain using sample text",
    long_description=long_description,
    url="https://github.com/kwkelly/MarkovText",
    author="Keith Kelly",
    author_email="k3ithk@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    keywords="markov chain text generator",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=["numpy"],
)
