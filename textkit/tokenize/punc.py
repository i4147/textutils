import re
from string import punctuation
import click
from textkit.utils import output


@click.command()
@click.argument("text", type=click.Path(exists=True), nargs=-1)
def text2punc(text):
    content = "\n".join([open(f).read() for f in text])
    out = re.sub(r"[^{}]+".format(punctuation), " ", content)
    out = out.split()
    [output(p) for p in out]
