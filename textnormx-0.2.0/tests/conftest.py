import pytest


@pytest.fixture
def md_sample():
    return """
# Title A

Paragraph one line one.

Paragraph two continues here.

- Bullet A
1. Bullet B

| Col1 | Col2 |
| ---- | ---- |
|  A   |  B   |

## Subtitle B

This is a long paragraph intended to be split into several chunks by the chunker. It keeps going with
more sentences to ensure we exceed the chunk_size threshold. Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Donec a diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula ac quam
vulputate, nec ultricies sapien placerat. Integer vitae justo eget magna fermentum iaculis.
""".strip()
