from setuptools import setup


def readme():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="Coltext",
    version="1.0",
    author="filcher2011",
    author_email="filcher2011@mail.ru",
    description="Coltext - an alternative to colorama that can change the text color and background",
    long_description=readme(),
    long_description_content_type="text/markdown",
    packages=["Coltext"],
    install_requires=["requests>=2.25.1"],
    keywords="Coltext",
    python_requires=">=3.7",
)
