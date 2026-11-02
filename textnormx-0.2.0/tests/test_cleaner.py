from textnormx.cleaner.normalize import clean_chunks, clean_lines, clean_text
from textnormx.parser.types import Chunk


def test_clean_text_preserves_md_table():
    s = "| A |  B |\n| -- | -- |\n| 1  |  2 |"
    out = clean_text(s, preserve_markdown_tables=True)
    assert "| A |  B |" in out  # spacing preserved
    assert "\u00a0" not in out


def test_clean_lines_basic():
    lines = ["\uf0b7 bullet", "plain"]
    out = clean_lines(lines)
    assert "-" in out[0]
    assert "\uf0b7" not in out[0]
    assert out[1] == "plain"


def test_clean_chunks_dataclass_and_md_table():
    ch = Chunk(
        text="A \uf0b7 bullet\n| C1 | C2 |\n| -- | -- |",
        element_id="id",
        type="Text",
        metadata={"filename": "f", "filetype": "md", "page_number": 1, "parent_id": None, "coordinates": None},
    )
    clean_chunks([ch], preserve_markdown_tables=True)
    assert "-" in ch.text
    assert "\uf0b7" not in ch.text
    assert "| C1 | C2 |" in ch.text
