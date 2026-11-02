import os
import click
import nltk
from textkit.utils import output, read_tokens


@click.command("download")
def download():
    click.echo(
        "Installing nltk packages into your user directories in "
        "the following order of existence (first found):\n" + "\n".join(nltk.data.path)
    )
    extensions = [("taggers", "averaged_perceptron_tagger")]
    missing = check_packages_exist(extensions)
    for ext_tuple in missing:
        nltk.download(ext_tuple[1])


def check_packages_exist(extensions):
    paths = nltk.data.path
    missing = []
    ext_found = False
    for ext_tuple in extensions:
        click.echo(message="Looking for " + ext_tuple[1], nl=True)
        for path in paths:
            if os.path.exists(os.path.join(path, ext_tuple[0], ext_tuple[1])):
                ext_found = True
                click.echo(message="Found " + ext_tuple[1], nl=True)
                break
        if not ext_found:
            missing.append(ext_tuple)
    return missing
