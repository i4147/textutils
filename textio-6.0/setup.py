import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="textio",
    version="6.0",
    author="Monil Darediya",
    author_email="monildarediya1@gmail.com",
    description="A Text Library",
    long_description="""# About Module
Hey This Is A Module For Python It Makes Easy To Do Some Animated Text first do: `import textio`
textio has an alphs variable which has a list of alphabets
to import use: `textio.alphs` and textio also has a `renderText()` function which is different from `print()` you are thinking what is different from `print()` ? because this function has animated text it uses 2 args 1 is `string` 2 is `writetime` you can put `writetime` 0.1 to 0.10 now don't think more about `writetime`
put any number from this. then second function is `deleteText()` which will delete the `renderText()` you have written before it takes 1 arg wait which is how many seconds after it should delete the text thats the brief explaination of TextIO.
""",
    long_description_content_type="text/markdown",
    license="BSD",
    keywords="TextEdits",
    url="",
    packages=["textio"],
    classifiers=["Development Status :: 2 - Pre-Alpha", "Topic :: Utilities", "License :: OSI Approved :: BSD License"],
)
