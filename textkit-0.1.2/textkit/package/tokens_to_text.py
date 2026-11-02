import click
from textkit.utils import output, read_tokens


@click.command()
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
@click.option("--sep", default=" ", help="Separator between token and count in output.", show_default=True)
def tokens2text(sep, tokens):
    content = read_tokens(tokens)
    out = sep.join(content)
    output(out)
