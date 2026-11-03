from collections import namedtuple
import json
import sys
from typing import Union

import click
from pdfminer.layout import LTTextBox, LTAnno, LTChar
from pdfminer.high_level import extract_pages


BB = namedtuple('BB', ['x0', 'y0', 'x1', 'y1'])

def contained(query: BB, target: LTChar) -> bool:
    return query.x0 <= target.x0 and target.x1 <= query.x1 and \
           query.y0 <= target.y0 and target.y1 <= query.y1

def overlapping(query: BB, target: LTChar) -> bool:
    return not (query.x1 <= target.x0 or \
                target.x1 <= query.x0 or \
                query.y1 <= target.y0 or \
                target.y1 <= query.y0)

def chars_text(chars: list[Union[LTChar, LTAnno]]) -> str:
    return ''.join(c.get_text() for c in chars)

def bb_of(chars: list[Union[LTChar, LTAnno]]) -> BB:
    return BB(
        min(c.x0 for c in chars if isinstance(c, LTChar)),
        min(c.y0 for c in chars if isinstance(c, LTChar)),
        max(c.x1 for c in chars if isinstance(c, LTChar)),
        max(c.y1 for c in chars if isinstance(c, LTChar)),
    )


@click.command()
@click.option('--cover', type=click.Choice(['contain', 'overlap'], case_sensitive=False), required=True)
@click.argument('page_num', type=click.INT)
@click.argument('x', type=click.FLOAT)
@click.argument('y', type=click.FLOAT)
@click.argument('width', type=click.FLOAT)
@click.argument('height', type=click.FLOAT)
@click.argument('pdf_fp', type=click.Path(exists=True))
def main(page_num: int, x: float, y: float, width: float, height: float, pdf_fp: str, cover: str):
    query_page_num = page_num

    if cover == 'contain':
        covered = contained
    elif cover == 'overlap':
        covered = overlapping
    else:
        raise RuntimeError(f'Unknown cover type "{cover}".')

    for i, page in enumerate(extract_pages(pdf_fp)):
        page_num = i + 1
        if page_num != query_page_num:
            continue
        query = BB(x, page.height - y - height, x + width, page.height - y)
        matched_lines = []
        for elem in page:
            if isinstance(elem, LTTextBox):
                assert (elem.bbox) == (elem.x0, elem.y0, elem.x1, elem.y1)
                text_box = elem
                for line in text_box:
                    matched_chars = []
                    for char in line:
                        # TextLineElement = Union[LTChar, LTAnno]
                        if isinstance(char, LTChar):
                            assert char.x1 - char.x0 > 0
                            assert char.y1 - char.y0 > 0
                            if covered(query, char):
                                matched_chars.append(char)
                            elif len(matched_chars) > 0:
                                # Nothing left can be a matched char
                                # This is needed to prevent trailing LTAnno to be included
                                break
                        elif isinstance(char, LTAnno):
                            if char.get_text() != '\n':
                                if len(matched_chars) > 0:
                                    matched_chars.append(char)
                                else:
                                    # Ignore leading LTAnno
                                    pass
                    if len(matched_chars) > 0:
                        matched_lines.append(matched_chars)
        # Print results
        for line in matched_lines:
            bb = bb_of(line)
            result = dict(
                text=chars_text(line),
                x1=bb.x0,
                y1=bb.y0,
                x2=bb.x1,
                y2=bb.y1,
            )
            json.dump(result, sys.stdout, ensure_ascii=False)
            sys.stdout.write('\n')
        # Specified page has been processed
        break


if __name__ == '__main__':
    main()
