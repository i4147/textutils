import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="pygametext",
    version="0.1.0.1",
    author="LeBogo",
    author_email="lebogomc@gmail.com",
    description="This Package adds UI Elements like Buttons and Textboxes to PyGame.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeBogoo/pygametext",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
