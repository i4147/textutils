import click
from textkit.utils import read_tokens, write_csv


@click.command("tokens2counts")
@click.argument("tokens", type=click.File("r"), default=click.open_file("-"))
@click.option("--sep", default=",", help="Separator between token and count in output.", show_default=True)
@click.option("--limit", default=-1, type=click.INT, help="Only output the top N most frequent tokens")
def tokens2counts(sep, limit, tokens):
    content = read_tokens(tokens)
    counts = sort_counts(get_counts(content))
    if limit < 0:
        limit = float("inf")
    rows = [map(str, vals) for ind, vals in enumerate(counts) if ind < limit]
    write_csv(rows, sep)


def get_counts(tokens):
    counts = {}
    for token in tokens:
        if token in counts:
            counts[token] += 1
        else:
            counts[token] = 1
    return counts


def sort_counts(counts):
    return sorted(counts.items(), key=lambda count: count[1], reverse=True)
