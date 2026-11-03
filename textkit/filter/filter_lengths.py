import click
from textkit.utils import output, read_tokens


@click.command()
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
@click.option("-m", "--minimum", default=3, help="Minimum length of token to not filter.", show_default=True)
def filterlengths(minimum, tokens):
    content = read_tokens(tokens)
    [output(token) for token in content if len(token) >= minimum]
