from setuptools import setup, find_packages
from codecs import open
from os import path
import unittest


def audio2text_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests")
    return test_suite


here = path.abspath(path.dirname(__file__))
setup(
    name="audio2text",
    version="1.0.0",
    description="This package is for extract text from audio/video file",
    url="https://github.com/LG-1/audio2text",
    author="LG",
    author_email="ourantech@163.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="speech-recognition stt asr english speech-to-text",
    packages=find_packages(exclude=["audio2text", "models", "tests"]),
    install_requires=["torch", "torchaudio", "numpy", "pandas"],
    extras_require={
        "dev": ["check-manifest", "sphinx", "sphinx_rtd_theme"],
        "test": ["coverage", "nose"],
    },
    package_data={},
    data_files=[],
    entry_points={},
    test_suite="setup.audio2text_test_suite",
)
