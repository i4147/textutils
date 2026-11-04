import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from . import __version__
from .cleaner import TextCleaner
from .formatters import (
    format_clauses,
    format_paragraphs,
    format_sentences,
    split_long_lines,
)
from .models import Chapter, Metadata, Page, PageSource
from .parser import EPUBParser

console = Console()

MAX_DESCRIPTION_LENGTH = 200


@contextmanager
def spinner(task_description: str) -> Iterator[None]:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(task_description, total=None)
        yield


def parse_range_tokens(range_str: str) -> list[tuple[str, str | None]]:
    if not range_str:
        raise ValueError("Range string cannot be empty")

    tokens: list[tuple[str, str | None]] = []
    parts = range_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            raise ValueError("Range contains empty value")
        if "-" in part:
            start, end = part.split("-", 1)
            start = start.strip()
            end = end.strip()
            if not start or not end:
                raise ValueError(f"Invalid range segment: '{part}'")
            tokens.append((start, end))
        else:
            tokens.append((part, None))

    return tokens


def parse_chapter_range(range_str: str) -> list[int]:
    indices: list[int] = []
    seen: set[int] = set()

    for start, end in parse_range_tokens(range_str):
        if end is None:
            idx = int(start) - 1
            if idx not in seen:
                indices.append(idx)
                seen.add(idx)
            continue

        start_idx = int(start) - 1
        end_idx = int(end) - 1
        if start_idx > end_idx:
            raise ValueError(f"Invalid range: start '{start}' must be <= end '{end}'")
        for idx in range(start_idx, end_idx + 1):
            if idx not in seen:
                indices.append(idx)
                seen.add(idx)

    return indices


def display_chapters_tree(chapters: list[Chapter]) -> None:
    tree = Tree("📚 [bold]Chapters[/bold]")

    chapter_nodes = {}
    for chapter in chapters:
        label = (
            f"[cyan]{chapter.title}[/cyan] [dim]({chapter.char_count:,} chars)[/dim]"
        )

        if chapter.parent_id is None:
            node = tree.add(label)
            chapter_nodes[chapter.id] = node
        else:
            parent_node = chapter_nodes.get(chapter.parent_id)
            if parent_node:
                node = parent_node.add(label)
                chapter_nodes[chapter.id] = node
            else:
                node = tree.add(label)
                chapter_nodes[chapter.id] = node

    console.print(tree)


def display_chapters_table(chapters: list[Chapter]) -> None:
    table = Table(title="📚 Chapters", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("Title", style="cyan")
    table.add_column("Characters", justify="right", style="green")
    table.add_column("Level", justify="center", style="yellow")

    for idx, chapter in enumerate(chapters, 1):
        indent = "  " * (chapter.level - 1)
        title = f"{indent}{chapter.title}"
        table.add_row(str(idx), title, f"{chapter.char_count:,}", str(chapter.level))

    console.print(table)


def display_pages_table(pages: list[Page]) -> None:
    table = Table(title="📄 Pages", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("Page", style="cyan", width=10)
    table.add_column("Characters", justify="right", style="green")
    table.add_column("Source", justify="center", style="yellow")
    table.add_column("Chapter", style="blue")

    for idx, page in enumerate(pages, 1):
        source_str = (
            "print" if page.source == PageSource.EPUB_PAGE_LIST else "synthetic"
        )
        chapter_str = page.chapter_title or "-"
        if len(chapter_str) > 40:
            chapter_str = chapter_str[:37] + "..."
        table.add_row(
            str(idx),
            page.page_number,
            f"{page.char_count:,}",
            source_str,
            chapter_str,
        )

    console.print(table)


def parse_page_range(range_str: str, pages: list[Page]) -> list[str]:
    valid_page_numbers = {p.page_number for p in pages}
    numeric_page_numbers = {
        int(p.page_number) for p in pages if p.page_number.isdigit()
    }
    result: list[str] = []
    seen: set[str] = set()

    def parse_int(value: str) -> int | None:
        try:
            return int(value)
        except ValueError:
            return None

    def add_page_number(page_number: str) -> None:
        if page_number not in seen:
            result.append(page_number)
            seen.add(page_number)

    for start, end in parse_range_tokens(range_str):
        if end is None:
            if start in valid_page_numbers:
                add_page_number(start)
                continue

            idx = parse_int(start)
            if idx is not None and 0 < idx <= len(pages):
                add_page_number(pages[idx - 1].page_number)
            continue

        start_idx = parse_int(start)
        end_idx = parse_int(end)
        if start_idx is not None and end_idx is not None:
            if start_idx > end_idx:
                raise ValueError(
                    f"Invalid range: start '{start}' must be <= end '{end}'"
                )
            literal_matches = False
            if numeric_page_numbers:
                for page in pages:
                    page_num = parse_int(page.page_number)
                    if page_num is None:
                        continue
                    if start_idx <= page_num <= end_idx:
                        add_page_number(page.page_number)
                        literal_matches = True

            if not literal_matches:
                for idx in range(start_idx - 1, end_idx):
                    if 0 <= idx < len(pages):
                        add_page_number(pages[idx].page_number)
            continue

        if start in valid_page_numbers:
            add_page_number(start)
        if end in valid_page_numbers:
            add_page_number(end)

    return result


def interactive_chapter_selection(chapters: list[Chapter]) -> list[str]:
    console.print("\n[bold]Interactive Chapter Selection[/bold]")
    console.print(
        "Enter chapter numbers or ranges (e.g., '1-5,7,9-12'), "
        "or 'all' for all chapters:"
    )

    while True:
        selection = Prompt.ask("\n[cyan]Chapters to extract[/cyan]", default="all")

        if selection.lower() == "all":
            return [ch.id for ch in chapters]

        try:
            indices = parse_chapter_range(selection)
            valid_indices = [i for i in indices if 0 <= i < len(chapters)]
            if not valid_indices:
                console.print("[red]No valid chapter indices found. Try again.[/red]")
                continue

            selected_chapters = [chapters[i] for i in valid_indices]

            console.print(
                f"\n[green]Selected {len(selected_chapters)} chapter(s):[/green]"
            )
            for chapter in selected_chapters:
                console.print(f"  • {chapter.title}")

            if Confirm.ask("\nProceed with this selection?", default=True):
                return [ch.id for ch in selected_chapters]

        except (ValueError, IndexError) as e:
            console.print(f"[red]Invalid input: {e}. Try again.[/red]")


@click.group()
@click.version_option(version=__version__, prog_name="epub2text")
def cli() -> None:
    pass


def wrap_text_gutenberg(text: str, width: int = 72) -> str:
    import textwrap

    paragraphs = text.split("\n\n")
    wrapped_paragraphs = []

    for para in paragraphs:
        if para.strip():
            wrapped = textwrap.fill(
                para, width=width, break_long_words=False, break_on_hyphens=False
            )
            wrapped_paragraphs.append(wrapped)
        else:
            wrapped_paragraphs.append(para)

    return "\n\n".join(wrapped_paragraphs)


def generate_gutenberg_header(metadata: "Metadata", title: str) -> str:
    from datetime import datetime

    lines = []

    lines.append(f"The Project Gutenberg eBook of {title}")
    lines.append("")

    lines.append(
        "This ebook is for the use of anyone anywhere in the United States and"
    )
    lines.append(
        "most other parts of the world at no cost and with almost no restrictions"
    )
    lines.append(
        "whatsoever. You may copy it, give it away or re-use it under the terms"
    )
    lines.append("of the Project Gutenberg License included with this ebook or online")
    lines.append("at www.gutenberg.org. If you are not located in the United States,")
    lines.append("you will have to check the laws of the country where you are located")
    lines.append("before using this eBook.")
    lines.append("")

    lines.append(f"Title: {title}")
    lines.append("")

    if metadata.authors:
        author_str = ", ".join(metadata.authors)
        lines.append(f"Author: {author_str}")
        lines.append("")

    current_date = datetime.now().strftime("%B %d, %Y")
    lines.append(f"Release date: {current_date} [Generated by epub2text]")
    lines.append("")

    if metadata.language:
        lang_name = metadata.language
        lang_map = {
            "en": "English",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
        }
        lang_name = lang_map.get(metadata.language.lower(), metadata.language)
        lines.append(f"Language: {lang_name}")
        lines.append("")

    lines.append("")
    lines.append(f"*** START OF THE PROJECT GUTENBERG EBOOK {title.upper()} ***")
    lines.append("")

    return "\n".join(lines)


def generate_table_of_contents(chapters: list["Chapter"]) -> str:
    lines = []
    lines.append("Contents")
    lines.append("")
    lines.append("")

    for chapter in chapters:
        indent = " " * (chapter.level - 1)
        lines.append(f"{indent}{chapter.title.upper()}")
        lines.append("")

    return "\n".join(lines)


@cli.command(name="list")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "tree"]),
    default="table",
    help="Display format for chapters",
)
def list_chapters(filepath: Path, format: str) -> None:
    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath))
            chapters = parser.get_chapters()

        if not chapters:
            console.print("[yellow]No chapters found in EPUB file.[/yellow]")
            return

        console.print(
            f"\n[bold]Found {len(chapters)} chapter(s) in {filepath.name}[/bold]\n"
        )

        if format == "tree":
            display_chapters_tree(chapters)
        else:
            display_chapters_table(chapters)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command(name="pages")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--page-size",
    "-s",
    type=int,
    default=2000,
    help="Synthetic page size in characters (default: 2000)",
)
@click.option(
    "--use-words",
    "-w",
    is_flag=True,
    help="Use word count instead of character count for synthetic pages",
)
def list_pages(filepath: Path, page_size: int, use_words: bool) -> None:
    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath))
            all_pages = parser.get_pages(
                synthetic_page_size=page_size,
                use_words=use_words,
            )
            has_page_list = any(
                page.source == PageSource.EPUB_PAGE_LIST for page in all_pages
            )

        if not all_pages:
            console.print("[yellow]No pages found in EPUB file.[/yellow]")
            return

        if has_page_list:
            console.print(
                f"\n[bold]Found {len(all_pages)} page(s) from EPUB page-list "
                f"in {filepath.name}[/bold]"
            )
            console.print(
                "[dim](These correspond to original print book pages)[/dim]\n"
            )
        else:
            unit = "words" if use_words else "characters"
            console.print(
                f"\n[bold]Generated {len(all_pages)} synthetic page(s) "
                f"in {filepath.name}[/bold]"
            )
            console.print(
                f"[dim](No page-list found, using ~{page_size:,} {unit} "
                f"per page)[/dim]\n"
            )

        display_pages_table(all_pages)

        total_chars = sum(p.char_count for p in all_pages)
        console.print(f"\n[dim]Total: {total_chars:,} characters[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command(name="extract-pages")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--pages",
    "-p",
    type=str,
    help=(
        "Page range (e.g., '1-5,7,9-12'); prefers literal page numbers "
        "when available, otherwise uses 1-based indices"
    ),
)
@click.option(
    "--page-size",
    "-s",
    type=int,
    default=2000,
    help="Synthetic page size in characters (default: 2000)",
)
@click.option(
    "--use-words",
    "-w",
    is_flag=True,
    help="Use word count instead of character count for synthetic pages",
)
@click.option("--raw", is_flag=True, help="Disable all text cleaning")
@click.option(
    "--no-markers",
    is_flag=True,
    help="Hide <<PAGE: ...>> markers and chapter titles from output",
)
@click.option(
    "--show-front-matter",
    is_flag=True,
    help="Show front matter (TOC, Acknowledgements, etc.) - default is to hide",
)
@click.option(
    "--keep-duplicate-titles",
    is_flag=True,
    help="Keep duplicate chapter titles in page content (don't deduplicate)",
)
def extract_pages_cmd(
    filepath: Path,
    output: Path | None,
    pages: str | None,
    page_size: int,
    use_words: bool,
    raw: bool,
    no_markers: bool,
    show_front_matter: bool,
    keep_duplicate_titles: bool,
) -> None:
    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath), paragraph_separator="\n\n")
            all_pages = parser.get_pages(
                synthetic_page_size=page_size,
                use_words=use_words,
            )
            has_page_list = any(
                page.source == PageSource.EPUB_PAGE_LIST for page in all_pages
            )

        if not all_pages:
            console.print("[yellow]No pages found in EPUB file.[/yellow]")
            return

        if has_page_list:
            console.print(
                f"[dim]Using {len(all_pages)} pages from EPUB page-list[/dim]",
            )
        else:
            unit = "words" if use_words else "characters"
            console.print(
                f"[dim]Generated {len(all_pages)} synthetic pages "
                f"(~{page_size:,} {unit} each)[/dim]",
            )

        page_numbers = None
        if pages:
            try:
                page_numbers = parse_page_range(pages, all_pages)
                if not page_numbers:
                    console.print("[red]No valid pages found in range.[/red]")
                    sys.exit(1)
            except (ValueError, IndexError) as e:
                console.print(f"[red]Invalid page range: {e}[/red]")
                sys.exit(1)

        with spinner("Extracting pages..."):
            text = parser.extract_pages(
                page_numbers=page_numbers,
                deduplicate_chapter_titles=not keep_duplicate_titles,
                skip_toc=not show_front_matter,
            )

        if no_markers:
            text = re.sub(r"<<PAGE:[^>]*>>\n*", "", text)
            text = re.sub(r"\n{4,}[^\n]+\n{2,}", "\n\n", text)

        if not raw:
            cleaner = TextCleaner(
                remove_footnotes=True,
                remove_page_numbers=True,
                preserve_single_newlines=False,
            )
            with spinner("Cleaning text..."):
                text = cleaner.clean(text)

        if output:
            output.write_text(text, encoding="utf-8")
            console.print(
                f"\n[green]✓[/green] Extracted {len(text):,} characters to {output}"
            )
        else:
            print(text)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option("--chapters", "-c", type=str, help="Chapter range (e.g., '1-5,7,9-12')")
@click.option("--interactive", "-i", is_flag=True, help="Interactive chapter selection")
@click.option(
    "--paragraphs",
    "-p",
    is_flag=True,
    help="One line per paragraph (collapse internal line breaks)",
)
@click.option(
    "--sentences",
    "-s",
    is_flag=True,
    help="One line per sentence (uses spaCy)",
)
@click.option(
    "--comma",
    is_flag=True,
    help="One line per clause/comma-separated part (uses spaCy)",
)
@click.option(
    "--max-length",
    "-m",
    type=int,
    default=None,
    help="Split lines exceeding N chars at clause boundaries (uses spaCy)",
)
@click.option(
    "--empty-lines",
    is_flag=True,
    help="Use empty lines between paragraphs (instead of default separator)",
)
@click.option(
    "--separator",
    type=str,
    default="  ",
    help="Paragraph separator prepended to new paragraphs (default: two spaces)",
)
@click.option("--raw", is_flag=True, help="Disable all text cleaning")
@click.option(
    "--keep-footnotes", is_flag=True, help="Keep bracketed footnotes like [1]"
)
@click.option("--keep-page-numbers", is_flag=True, help="Keep page numbers")
@click.option(
    "--no-markers",
    is_flag=True,
    help="Hide chapter titles from output",
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    show_default=True,
    help="Output representation.",
)
@click.option(
    "--language-model",
    "-l",
    type=str,
    default="en_core_web_sm",
    help="spaCy language model (default: en_core_web_sm)",
)
@click.option(
    "--offset",
    type=int,
    default=0,
    help="Skip the first N lines of output",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit output to N lines",
)
@click.option(
    "--line-numbers",
    "-n",
    is_flag=True,
    help="Add line numbers to output",
)
def extract(
    filepath: Path,
    output: Path | None,
    chapters: str | None,
    interactive: bool,
    paragraphs: bool,
    sentences: bool,
    comma: bool,
    max_length: int | None,
    empty_lines: bool,
    separator: str,
    raw: bool,
    keep_footnotes: bool,
    keep_page_numbers: bool,
    no_markers: bool,
    output_format: str,
    language_model: str,
    offset: int,
    limit: int | None,
    line_numbers: bool,
) -> None:
    try:
        if output_format == "markdown":
            incompatible = []
            if paragraphs:
                incompatible.append("--paragraphs")
            if sentences:
                incompatible.append("--sentences")
            if comma:
                incompatible.append("--comma")
            if max_length is not None:
                incompatible.append("--max-length")
            if incompatible:
                raise click.UsageError(
                    "Markdown output is incompatible with formatting options: "
                    + ", ".join(incompatible)
                )
            with spinner(f"Loading {filepath.name}..."):
                parser = EPUBParser(str(filepath), paragraph_separator="\n\n")
                chapter_documents = parser.get_chapter_documents()
            if chapters:
                try:
                    indices = parse_chapter_range(chapters)
                    selected_documents = [
                        chapter_documents[index]
                        for index in indices
                        if 0 <= index < len(chapter_documents)
                    ]
                except (ValueError, IndexError) as exc:
                    raise click.UsageError(f"Invalid chapter range: {exc}") from exc
            else:
                selected_documents = chapter_documents
            with spinner("Extracting Markdown chapters..."):
                text = "\n".join(
                    document.to_markdown(include_title=not no_markers)
                    for document in selected_documents
                )
            if text and not text.endswith("\n"):
                text += "\n"
            if output:
                output.write_text(text, encoding="utf-8")
                console.print(
                    f"\n[green]✓[/green] Extracted {len(text):,} characters to {output}"
                )
            else:
                print(text, end="")
            return

        effective_separator = "" if empty_lines else separator

        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath), paragraph_separator="\n\n")
            all_chapters = parser.get_chapters()

        if not all_chapters:
            console.print("[yellow]No chapters found in EPUB file.[/yellow]")
            return

        chapter_ids = None
        if interactive:
            display_chapters_table(all_chapters)
            chapter_ids = interactive_chapter_selection(all_chapters)
        elif chapters:
            try:
                indices = parse_chapter_range(chapters)
                chapter_ids = [
                    all_chapters[i].id for i in indices if 0 <= i < len(all_chapters)
                ]
            except (ValueError, IndexError) as e:
                console.print(f"[red]Invalid chapter range: {e}[/red]")
                sys.exit(1)

        with spinner("Extracting chapters..."):
            text = parser.extract_chapters(chapter_ids)

        if no_markers:
            text = re.sub(
                r"(^|\n{4,})[^\n]+\n{2,}",
                "\n\n",
                text,
                count=0,
                flags=re.MULTILINE,
            )

        if not raw:
            cleaner = TextCleaner(
                remove_footnotes=not keep_footnotes,
                remove_page_numbers=not keep_page_numbers,
                preserve_single_newlines=True,
            )
            with spinner("Cleaning text..."):
                text = cleaner.clean(text)

        if sentences and comma:
            with spinner("Formatting sentences and clauses..."):
                try:
                    text = format_sentences(
                        text,
                        separator=effective_separator,
                        language_model=language_model,
                    )
                    text = format_clauses(
                        text,
                        separator=effective_separator,
                        language_model=language_model,
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif comma:
            with spinner("Formatting clauses..."):
                try:
                    text = format_clauses(
                        text,
                        separator=effective_separator,
                        language_model=language_model,
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif sentences:
            with spinner("Formatting sentences..."):
                try:
                    text = format_sentences(
                        text,
                        separator=effective_separator,
                        language_model=language_model,
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif paragraphs or not empty_lines:
            with spinner("Formatting paragraphs..."):
                text = format_paragraphs(
                    text,
                    separator=effective_separator,
                    one_line_per_paragraph=paragraphs,
                )

        if max_length is not None:
            with spinner("Splitting long lines..."):
                try:
                    text = split_long_lines(
                        text,
                        max_length=max_length,
                        separator=effective_separator,
                        language_model=language_model,
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)

        if offset > 0 or limit is not None or line_numbers:
            lines = text.splitlines()
            total_lines = len(lines)

            if offset > 0:
                if offset >= total_lines:
                    lines = []
                else:
                    lines = lines[offset:]

            if limit is not None and limit > 0:
                lines = lines[:limit]

            if line_numbers:
                start_line = offset + 1
                end_line = start_line + len(lines)
                width = len(str(end_line))
                lines = [
                    f"{start_line + i:{width}d}\t{line}" for i, line in enumerate(lines)
                ]

            text = "\n".join(lines)

        if output:
            output.write_text(text, encoding="utf-8")
            console.print(
                f"\n[green]✓[/green] Extracted {len(text):,} characters to {output}"
            )
        else:
            print(text)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command(name="extract-gutenberg")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path (default: {book-title}.txt)",
)
@click.option(
    "--chapters",
    "-c",
    type=str,
    default=None,
    help="Chapter range to extract (e.g., '1-5,7,9-12')",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Interactive chapter selection",
)
def extract_gutenberg(
    filepath: Path,
    output: Path | None,
    chapters: str | None,
    interactive: bool,
) -> None:
    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath), paragraph_separator="\n\n")
            metadata = parser.get_metadata()
            all_chapters = parser.get_chapters()

        if not all_chapters:
            console.print("[yellow]No chapters found in EPUB file.[/yellow]")
            return

        title = metadata.title or "Unknown Title"

        chapter_ids = None
        selected_chapters = all_chapters

        if interactive:
            display_chapters_table(all_chapters)
            chapter_ids = interactive_chapter_selection(all_chapters)
            selected_chapters = [ch for ch in all_chapters if ch.id in chapter_ids]
        elif chapters:
            try:
                indices = parse_chapter_range(chapters)
                chapter_ids = [
                    all_chapters[i].id for i in indices if 0 <= i < len(all_chapters)
                ]
                selected_chapters = [ch for ch in all_chapters if ch.id in chapter_ids]
            except (ValueError, IndexError) as e:
                console.print(f"[red]Invalid chapter range: {e}[/red]")
                sys.exit(1)

        book_parts = []

        with spinner("Generating header..."):
            header = generate_gutenberg_header(metadata, title)
            book_parts.append(header)

        book_parts.append(title)
        book_parts.append("")
        if metadata.authors:
            author_str = ", ".join(metadata.authors)
            book_parts.append(f"by {author_str}")
            book_parts.append("")

        front_matter_titles = {
            "INTRODUCTION",
            "CONTENTS",
            "ACKNOWLEDGEMENTS",
            "FOREWORD",
            "PREFACE",
            "ACKNOWLEDGMENTS",
        }
        content_chapters = [
            ch
            for ch in selected_chapters
            if ch.title.upper() not in front_matter_titles
        ]

        book_parts.append("")
        toc = generate_table_of_contents(content_chapters)
        book_parts.append(toc)

        with spinner("Extracting chapters..."):
            chapter_text = parser.extract_chapters(chapter_ids)

            cleaner = TextCleaner(
                remove_footnotes=True,
                remove_page_numbers=True,
                preserve_single_newlines=False,
            )
            chapter_text = cleaner.clean(chapter_text)

        with spinner("Formatting chapters..."):
            chapter_lines = chapter_text.split("\n")

            current_title: str | None = None
            current_content: list[str] = []
            chapters_list: list[tuple[str, str]] = []

            i = 0
            while i < len(chapter_lines):
                line = chapter_lines[i]

                if line.strip():
                    empty_before = 0
                    j = i - 1
                    while j >= 0 and not chapter_lines[j].strip():
                        empty_before += 1
                        j -= 1

                    empty_after = 0
                    j = i + 1
                    while j < len(chapter_lines) and not chapter_lines[j].strip():
                        empty_after += 1
                        j += 1

                    is_chapter_title = (
                        i == 0 or empty_before >= 4
                    ) and empty_after >= 2

                    if is_chapter_title:
                        if current_title is not None:
                            chapters_list.append(
                                (current_title, "\n".join(current_content).strip())
                            )

                        current_title = line.strip()
                        current_content = []
                        i += 1 + empty_after
                        continue

                if line.strip() or current_content:
                    current_content.append(line)

                i += 1

            if current_title is not None:
                chapters_list.append(
                    (current_title, "\n".join(current_content).strip())
                )

            for chapter_title, chapter_content in chapters_list:
                if chapter_title.upper() in front_matter_titles:
                    continue

                if chapter_content:
                    book_parts.append("")
                    book_parts.append("")
                    book_parts.append("")

                    book_parts.append(chapter_title.upper())
                    book_parts.append("")

                    formatted_content = wrap_text_gutenberg(chapter_content, width=72)
                    book_parts.append(formatted_content)

        final_text = "\n".join(book_parts)

        if output is None:
            safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "-")
            output = Path(f"{safe_title}.txt")

        output.write_text(final_text, encoding="utf-8")
        console.print(
            f"\n[green]✓[/green] Extracted {len(final_text):,} characters to {output}"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["panel", "table", "json"]),
    default="panel",
    help="Display format for metadata (default: panel)",
)
def info(filepath: Path, format: str) -> None:
    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath))
            metadata = parser.get_metadata()
            chapters = parser.get_chapters()
            has_page_list = parser.has_page_list()

        total_chars = sum(ch.char_count for ch in chapters)

        if has_page_list:
            pages = parser.get_pages()
            page_count = len(pages)
            page_source = "print"
        else:
            page_count = max(1, total_chars // 2000)
            page_source = "estimated"

        if format == "table":
            table = Table(
                title=f"📖 {filepath.name}",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            if metadata.title:
                table.add_row("Title", metadata.title)
            if metadata.authors:
                table.add_row("Authors", ", ".join(metadata.authors))
            if metadata.contributors:
                table.add_row("Contributors", ", ".join(metadata.contributors))
            if metadata.publisher:
                table.add_row("Publisher", metadata.publisher)
            if metadata.publication_year:
                table.add_row("Year", metadata.publication_year)
            if metadata.identifier:
                table.add_row("Identifier", metadata.identifier)
            if metadata.language:
                table.add_row("Language", metadata.language)
            if metadata.rights:
                table.add_row("Rights", metadata.rights)
            if metadata.coverage:
                table.add_row("Coverage", metadata.coverage)
            if metadata.description:
                desc = (
                    metadata.description[:MAX_DESCRIPTION_LENGTH] + "..."
                    if len(metadata.description) > MAX_DESCRIPTION_LENGTH
                    else metadata.description
                )
                table.add_row("Description", desc)
            table.add_row("Chapters", str(len(chapters)))
            if page_source == "print":
                table.add_row("Pages", f"{page_count} (from page-list)")
            else:
                table.add_row("Pages", f"~{page_count} (estimated)")
            table.add_row("Total Characters", f"{total_chars:,}")

            console.print(table)
        elif format == "json":
            import json

            data = {
                "file": filepath.name,
                "title": metadata.title,
                "authors": metadata.authors,
                "contributors": metadata.contributors,
                "publisher": metadata.publisher,
                "publication_year": metadata.publication_year,
                "identifier": metadata.identifier,
                "language": metadata.language,
                "rights": metadata.rights,
                "coverage": metadata.coverage,
                "description": metadata.description,
                "chapters": len(chapters),
                "pages": page_count,
                "has_page_list": has_page_list,
                "total_characters": total_chars,
            }
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            info_lines = []
            if metadata.title:
                info_lines.append(f"[bold]Title:[/bold] {metadata.title}")
            if metadata.authors:
                authors_str = ", ".join(metadata.authors)
                info_lines.append(f"[bold]Authors:[/bold] {authors_str}")
            if metadata.contributors:
                contributors_str = ", ".join(metadata.contributors)
                info_lines.append(f"[bold]Contributors:[/bold] {contributors_str}")
            if metadata.publisher:
                info_lines.append(f"[bold]Publisher:[/bold] {metadata.publisher}")
            if metadata.publication_year:
                info_lines.append(f"[bold]Year:[/bold] {metadata.publication_year}")
            if metadata.identifier:
                info_lines.append(f"[bold]Identifier:[/bold] {metadata.identifier}")
            if metadata.language:
                info_lines.append(f"[bold]Language:[/bold] {metadata.language}")
            if metadata.rights:
                info_lines.append(f"[bold]Rights:[/bold] {metadata.rights}")
            if metadata.coverage:
                info_lines.append(f"[bold]Coverage:[/bold] {metadata.coverage}")
            if metadata.description:
                desc = (
                    metadata.description[:MAX_DESCRIPTION_LENGTH] + "..."
                    if len(metadata.description) > MAX_DESCRIPTION_LENGTH
                    else metadata.description
                )
                info_lines.append(f"[bold]Description:[/bold] {desc}")

            info_lines.append(f"\n[bold]Chapters:[/bold] {len(chapters)}")
            if page_source == "print":
                info_lines.append(f"[bold]Pages:[/bold] {page_count} (from page-list)")
            else:
                info_lines.append(f"[bold]Pages:[/bold] ~{page_count} (estimated)")
            info_lines.append(f"[bold]Total Characters:[/bold] {total_chars:,}")

            panel = Panel(
                "\n".join(info_lines), title=f"📖 {filepath.name}", border_style="cyan"
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--chapter", "-c", type=int, help="Start at specific chapter (number)")
@click.option("--line", "-l", type=int, help="Start at specific line number")
@click.option("--resume", is_flag=True, help="Resume from last bookmark")
@click.option(
    "--bookmark-file",
    type=click.Path(path_type=Path),
    help="Custom bookmark file path",
)
@click.option("--page-size", type=int, help="Lines per page (default: auto-detect)")
@click.option("--no-header", is_flag=True, help="Hide header")
@click.option("--no-footer", is_flag=True, help="Hide footer")
@click.option(
    "--sentences",
    "-s",
    is_flag=True,
    help="One sentence per line (uses spaCy)",
)
@click.option(
    "--comma",
    is_flag=True,
    help="One clause per line (uses spaCy)",
)
@click.option(
    "--paragraphs",
    "-p",
    is_flag=True,
    help="One paragraph per line",
)
@click.option(
    "--language-model",
    "-m",
    type=str,
    default="en_core_web_sm",
    help="spaCy language model (default: en_core_web_sm)",
)
@click.option("--raw", is_flag=True, help="Disable all text cleaning")
@click.option(
    "--keep-footnotes", is_flag=True, help="Keep bracketed footnotes like [1]"
)
@click.option("--keep-page-numbers", is_flag=True, help="Keep page numbers")
@click.option(
    "--width",
    "-w",
    type=int,
    help="Maximum content width for better readability (default: full terminal)",
)
def read(
    filepath: Path,
    chapter: int | None,
    line: int | None,
    resume: bool,
    bookmark_file: Path | None,
    page_size: int | None,
    no_header: bool,
    no_footer: bool,
    sentences: bool,
    comma: bool,
    paragraphs: bool,
    language_model: str,
    raw: bool,
    keep_footnotes: bool,
    keep_page_numbers: bool,
    width: int | None,
) -> None:
    from .bookmarks import BookmarkManager
    from .reader import EpubReader

    try:
        with spinner(f"Loading {filepath.name}..."):
            parser = EPUBParser(str(filepath), paragraph_separator="\n\n")
            all_chapters = parser.get_chapters()
            metadata = parser.get_metadata()

        if not all_chapters:
            console.print("[yellow]No chapters found in EPUB file.[/yellow]")
            return

        with spinner("Extracting chapters..."):
            text = parser.extract_chapters(None)

        if not raw:
            cleaner = TextCleaner(
                remove_footnotes=not keep_footnotes,
                remove_page_numbers=not keep_page_numbers,
                preserve_single_newlines=True,
            )
            with spinner("Cleaning text..."):
                text = cleaner.clean(text)

        if sentences and comma:
            with spinner("Formatting sentences and clauses..."):
                try:
                    text = format_sentences(
                        text, separator="  ", language_model=language_model
                    )
                    text = format_clauses(
                        text, separator="  ", language_model=language_model
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif comma:
            with spinner("Formatting clauses..."):
                try:
                    text = format_clauses(
                        text, separator="  ", language_model=language_model
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif sentences:
            with spinner("Formatting sentences..."):
                try:
                    text = format_sentences(
                        text, separator="  ", language_model=language_model
                    )
                except (ImportError, OSError) as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
        elif paragraphs:
            with spinner("Formatting paragraphs..."):
                text = format_paragraphs(
                    text, separator="  ", one_line_per_paragraph=True
                )
        else:
            with spinner("Formatting paragraphs..."):
                text = format_paragraphs(
                    text, separator="  ", one_line_per_paragraph=False
                )

        bookmark_manager = BookmarkManager(bookmark_file)

        start_line = 0
        start_chapter = None

        if resume:
            bookmark = bookmark_manager.load(str(filepath))
            if bookmark:
                start_line = bookmark.line_offset
                console.print(
                    f"[green]Resuming from {bookmark.percentage:.1f}%[/green]"
                )
            else:
                console.print(
                    "[yellow]No bookmark found, starting from beginning[/yellow]"
                )
        elif chapter is not None:
            start_chapter = chapter - 1
        elif line is not None:
            start_line = line - 1

        reader = EpubReader(
            content=text,
            chapters=all_chapters,
            title=metadata.title or filepath.name,
            epub_path=str(filepath),
            page_size=page_size,
            show_header=not no_header,
            show_footer=not no_footer,
            start_line=start_line,
            start_chapter=start_chapter,
            bookmark_manager=bookmark_manager,
            width=width,
        )

        reader.run()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command(name="inspect-structure")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Emit package inspection as JSON")
def inspect_structure(filepath: Path, as_json: bool) -> None:
    parser = EPUBParser(str(filepath))
    package = parser.inspect_package()
    if as_json:
        extraction = parser.extract_structured(include_segments=False)
        console.print(
            extraction.to_json(
                include_raw=False, include_runs=False, include_segments=False, indent=2
            )
        )
    else:
        console.print(f"Source: {package.source_path}")
        console.print(f"Spine items: {len(package.spine)}")
        console.print(f"Manifest items: {len(package.manifest_items)}")


@cli.command(name="extract-structure")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "output",
    type=click.Path(path_type=Path),
    help="Write JSON to this file",
)
@click.option(
    "--segments",
    type=click.Choice(["sentence", "paragraph", "clause"]),
    default=None,
    help="Include segments",
)
@click.option(
    "--include-runs/--no-runs", default=True, help="Include inline and text runs"
)
@click.option(
    "--raw/--no-raw", default=False, help="Include raw decoded source documents"
)
@click.option(
    "--xhtml-fragments/--no-xhtml-fragments",
    default=False,
    help="Include sanitized inline XHTML fragments in structured JSON output.",
)
@click.option(
    "--markdown-fragments/--no-markdown-fragments",
    default=False,
    help=(
        "Include Markdown translations of inline XHTML fragments in "
        "structured JSON output."
    ),
)
@click.option(
    "--markdown-flavor",
    type=click.Choice(["commonmark", "gfm"]),
    default="commonmark",
    show_default=True,
    help="Markdown flavor for inline fragment translation.",
)
def extract_structure(
    filepath: Path,
    output: Path | None,
    segments: str | None,
    include_runs: bool,
    raw: bool,
    xhtml_fragments: bool,
    markdown_fragments: bool,
    markdown_flavor: Literal["commonmark", "gfm"],
) -> None:
    parser = EPUBParser(str(filepath))
    extraction = parser.extract_structured(
        include_segments=segments is not None,
        segment_mode=segments or "sentence",
        include_xhtml_fragments=xhtml_fragments,
        include_markdown_fragments=markdown_fragments,
        markdown_flavor=markdown_flavor,
    )
    data = extraction.to_json(
        include_raw=raw,
        include_runs=include_runs,
        include_segments=segments is not None,
        include_xhtml_fragments=xhtml_fragments,
        include_markdown_fragments=markdown_fragments,
        indent=2,
    )
    if output:
        output.write_text(data, encoding="utf-8")
    else:
        click.echo(data)


@cli.command(name="validate-structure")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict-offsets",
    is_flag=True,
    help="Fail on structured extraction warnings and errors",
)
def validate_structure(filepath: Path, strict_offsets: bool) -> None:
    from .structured import ExtractionPolicy

    parser = EPUBParser(str(filepath))
    extraction = parser.extract_structured(
        policy=ExtractionPolicy(strict_offsets=strict_offsets), include_segments=True
    )
    errors = []
    docs = {doc.document_id: doc for doc in extraction.documents}
    for block in extraction.blocks:
        doc = docs[block.document_id]
        if not (0 <= block.outer_char_start <= block.outer_char_end <= len(doc.text)):
            errors.append(f"block range out of bounds: {block.id}")
        joined = "".join(getattr(run, "text", "") for run in block.runs)
        if joined != block.text:
            errors.append(f"run text mismatch: {block.id}")
    for segment in extraction.segments:
        block = next(
            block for block in extraction.blocks if block.id == segment.block_id
        )
        if (
            block.text[segment.block_text_start : segment.block_text_end]
            != segment.text
        ):
            errors.append(f"segment range mismatch: {segment.id}")
    if errors:
        for error in errors:
            console.print(f"[red]{error}[/red]")
        raise click.ClickException(f"{len(errors)} structured invariant(s) failed")
    console.print(
        f"[green]Structured extraction valid:[/green] "
        f"{len(extraction.blocks)} blocks, {len(extraction.segments)} segments"
    )


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
