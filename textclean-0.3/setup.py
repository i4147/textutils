from setuptools import setup

setup(
    name="textclean",
    packages=["textclean"],
    version="0.3",
    description="Handle the very famous decoding - encoding errors in Python !",
    author="Vikas Bharti",
    author_email="vikas.bharti.pro@gmail.com",
    long_description=open("README.rst").read(),
    include_package_data=True,
    package_data={
        "": ["*.txt"],
        "": ["textclean/*.txt"],
        "textclean": ["*.txt"],
    },
    license="MIT",
    classifiers=(
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ),
)
