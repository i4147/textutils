from setuptools import find_packages, setup

setup(
    name="lane4text",
    version="0.1.3",
    packages=find_packages(include=["lane4text", "lane4text.*", "lane4text.*.*"]),
    author="huangyongqi",
    description="带噪文本分类",
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
