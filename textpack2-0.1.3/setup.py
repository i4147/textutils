import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="textpack2",
    version="0.1.3",
    author="Luke Whyte",
    author_email="lukeawhyte@gmail.com",
    maintainer="Mikuláš Poul",
    maintainer_email="mikulaspoul@gmail.com",
    description="Quickly identify and group similar text strings in a large dataset",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xelixdev/textpack",
    packages=setuptools.find_packages(),
    install_requires=[
        "pandas",
        "scikit-learn",
        "scipy",
        "numpy",
        "cython",
        "sparse-dot-topn",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
