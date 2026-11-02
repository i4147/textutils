import logging
import re

from textnormx.cleaner.normalize import clean_chunks
from textnormx.parser import chunk_by_title, parse_markdown_elements


def test_parse_markdown_elements_basic(md_sample):
    elems = parse_markdown_elements(md_sample)
    types = [e.type for e in elems]
    assert types.count("Title") >= 2
    assert "Table" in types
    assert types.count("Text") >= 3
    assert elems[0].type == "Title"
    assert elems[0].text == "Title A"


def test_chunk_by_title_split_and_metadata(md_sample):
    elems = parse_markdown_elements(md_sample)
    chunks = chunk_by_title(
        elems,
        filename="ocr_result.md",
        filetype="md",
        chunk_size=120,  # small to force split
    )
    text_chunks = [c for c in chunks if c.type == "Text"]
    assert len(text_chunks) >= 2
    c0 = text_chunks[0]
    md = c0.metadata
    assert md["filename"] == "ocr_result.md"
    assert md["filetype"] == "md"
    assert isinstance(md["page_number"], int)
    assert md["parent_id"]
    assert re.match(r"^[0-9a-f-]{36}$", c0.element_id)


def test_chunk_by_title_tables_included(md_sample):
    elems = parse_markdown_elements(md_sample)
    chunks = chunk_by_title(elems, filename="with_table.md", filetype="md", chunk_size=200)
    table_chunks = [c for c in chunks if c.type == "Table"]
    assert len(table_chunks) >= 1
    assert table_chunks[0].text.splitlines()[0].startswith("|")


# def test_chunk_by_title_min_chars_excludes_tail():
#     md_small = "# Tiny\nShort."
#     elems = parse_markdown_elements(md_small)
#     chunks = chunk_by_title(elems, filename="tiny.md", filetype="md", chunk_size=500, min_chunk_chars=100)
#     assert all(c.type != "Text" for c in chunks)


def test_observation_results(md_sample):
    elems = parse_markdown_elements(md_sample)
    chunks = chunk_by_title(elems, filename="ocr_result.md", filetype="md", chunk_size=150)
    logging.info(f"Created {len(chunks)} chunks: {chunks}")
    logging.info("Cleaning chunk...")
    clean_chunk = clean_chunks(chunks, preserve_markdown_tables=True)
    logging.info(f"Cleaned {len(clean_chunk)} chunks: {clean_chunk}")
