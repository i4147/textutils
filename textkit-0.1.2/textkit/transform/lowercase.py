import click
from textkit.utils import output, read_tokens


@click.command()
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
def lowercase(tokens):
    content = read_tokens(tokens)
    [output(token.lower()) for token in content]
