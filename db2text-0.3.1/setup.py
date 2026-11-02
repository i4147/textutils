import setuptools, distutils, shutil, re, os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setuptools.setup(
    name="db2text",
    version="0.3.1",
    author="Chen chuan",
    author_email="kcchen@139.com",
    description="database to text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/chenc224/dbt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
    install_requires=["jinja2", "dbcfg", "PyPDF3"],
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "dbt=db2text.dbt:main",
            "db2text=db2text.dbt:main",
        ],
    },
)
