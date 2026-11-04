from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from kash.utils.common.url import Url

if TYPE_CHECKING:
    from kash.model import ActionResult


def help() -> None:
    from clideps.ui.rich_output import print_heading
    from kash.utils.rich_custom.rich_markdown_fork import Markdown
    from rich import print as rprint

    from textpress.cli.cli_docs import HELP_PAGE

    print_heading(message="Using Textpress")

    rprint()
    rprint(Markdown(HELP_PAGE))


def setup(show: bool = False) -> None:
    from textpress.cli.cli_setup import interactive_setup, show_setup

    if show:
        show_setup()
    else:
        interactive_setup()


def paste(title: str, plaintext: bool = False) -> Path:

    import pyperclip
    from kash.model import Format, Item, ItemType
    from kash.workspaces import current_ws

    contents = pyperclip.paste()
    if not contents.strip():
        raise ValueError("Clipboard is empty")

    ws = current_ws()
    format = Format.plaintext if plaintext else Format.markdown
    store_path = ws.save(Item(type=ItemType.resource, format=format, title=title, body=contents))

    return store_path


def files(all: bool = False) -> None:
    from kash.commands.base.files_command import files
    from kash.workspaces import current_ws
    from rich import print as rprint

    ws = current_ws()
    rprint()
    files(ws.base_dir, overview=True, all=all)


def convert(md_path: Path | Url, pdf_converter: str = "marker") -> ActionResult:
    from kash.exec import prepare_action_input
    from kash.kits.docs.actions.text.markdownify_doc import markdownify_doc

    input = prepare_action_input(md_path)
    return markdownify_doc(input, pdf_converter=pdf_converter)


def format(md_path: Path | Url, add_classes: str | None = None, no_minify: bool = False) -> ActionResult:
    from kash.exec import prepare_action_input

    from textpress.actions.textpress_format import textpress_format

    input = prepare_action_input(md_path)
    return textpress_format(input, add_classes=add_classes, no_minify=no_minify)


def publish(path: Path | Url, add_classes: str | None = None, no_minify: bool = False) -> ActionResult:
    from kash.exec import prepare_action_input

    from textpress.actions.textpress_publish import textpress_publish

    input = prepare_action_input(path)
    return textpress_publish(input, add_classes=add_classes, no_minify=no_minify)


def export(md_path: Path | Url) -> ActionResult:
    from kash.exec import prepare_action_input

    from textpress.actions.textpress_export import textpress_export

    input = prepare_action_input(md_path)
    return textpress_export(input)
