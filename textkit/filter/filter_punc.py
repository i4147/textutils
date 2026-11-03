from string import punctuation
import click
from textkit.utils import output, read_tokens


@click.command()
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
def filterpunc(tokens):
    content = read_tokens(tokens)
    [output(token) for token in content if token not in punctuation]
