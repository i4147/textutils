import click

from wetext import Normalizer


@click.command()
@click.argument("text")
@click.option("--lang", "-l", default="auto", type=click.Choice(["auto", "en", "zh", "ja"]))
@click.option("--operator", "-o", default="tn", type=click.Choice(["tn", "itn"]))
@click.option("--fix-contractions", is_flag=True, help="Fix contractions.")
@click.option("--traditional-to-simple", is_flag=True, help="Convert traditional Chinese to simplified Chinese.")
@click.option("--full-to-half", is_flag=True, help="Convert full-width characters to half-width characters.")
@click.option("--remove-interjections", is_flag=True, help="Remove interjections.")
@click.option("--remove-puncts", is_flag=True, help="Remove punctuation.")
@click.option("--tag-oov", is_flag=True, help="Tag out-of-vocabulary words.")
@click.option("--enable-0-to-9", is_flag=True, help="Enable 0-to-9 conversion.")
@click.option("--remove-erhua", is_flag=True, help="Remove erhua.")
def main(**kwargs):
    text = kwargs.pop("text")
    normalizer = Normalizer(**kwargs)
    text = normalizer.normalize(text)
    print(text)


if __name__ == "__main__":
    main()
