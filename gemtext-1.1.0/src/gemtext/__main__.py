import fileinput
from gemtext import Gemtext


def parse_input() -> None:
    with fileinput.input() as gemtext:
        for gem_line in Gemtext("".join(gemtext)).content:
            print(f"{gem_line!r}")


if __name__ == "__main__":
    parse_input()
