from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.rst").read_text(encoding="utf-8")
setup(
    name="Easytexts",
    version="1.1.0",
    author="Itamar Katzover",
    author_email="itamar43.katzover43@gmail.com",
    description="Easytexts: Simplified text management for quick and simple projects",
    long_description=long_description,
    url="https://github.com/Katzover/Easytexts",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.10",
)
