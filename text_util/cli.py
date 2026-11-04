import click
from clipboard_util import clipboard


@click.command()
@click.option("--to-dash-case", is_flag=True)
def cli(to_dash_case):

    clip_text = clipboard.get()
    print(f'original: "{clip_text}"')

    if to_dash_case:
        dashed_text = clip_text.replace("_", "-")
        print(f'dashed_text: "{dashed_text}"')
        clipboard.set(dashed_text)
        print("[copied to clipboard]")

    else:
        raise NotImplementedError


if __name__ == "__main__":
    cli()
