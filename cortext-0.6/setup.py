from distutils.core import setup

setup(
    name="cortext",
    packages=["cortext"],
    version="0.6",
    description="A text visualization library",
    author="Alexander Ivanov, Sophia Petrova",
    author_email="alehander42@gmail.com",
    url="https://github.com/kodki/cortext",
    download_url="https://github.com/kodki/cortext/tarball/0.2",
    keywords=["natural", "language"],
    install_requires=["nltk", "numpy", "flickrapi", "six"],
    classifiers=[],
)
