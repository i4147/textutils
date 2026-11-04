from pathlib import Path
from typing import Annotated

import typer

from .distance import levenshtein_distance
from .files import search_files
from .transform import leetspeak

app = typer.Typer(no_args_is_help=True, help="Linux text processing utilities.")


@app.command()
def distance(first: str, second: str) -> None:
    typer.echo(levenshtein_distance(first, second))


@app.command()
def leet(text: str) -> None:
    typer.echo(leetspeak(text))


@app.command()
def search(
    root: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    needle: str,
    pattern: str = "*.txt",
) -> None:
    try:
        for path, matches in search_files(root, needle, pattern):
            for line_number, line in matches:
                typer.echo(f"{path}:{line_number}:{line}")
    except (OSError, UnicodeError) as exc:
        typer.echo(f"Search failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
