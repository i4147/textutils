import os
import click
import nltk
from textkit.utils import data_item, output, read_tokens


@click.command("tokens2pos")
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
@click.option("--sep", default=" ", help="Separator between words in the output.", show_default=True)
def tokens2pos(sep, tokens):
    content = read_tokens(tokens)
    nltk.data.path.append(data_item())
    tags = nltk.pos_tag(content)
    [output("{},{}".format(t[0], t[1])) for t in tags]
