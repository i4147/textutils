import argparse
import sys

import numtext as nt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("_", nargs="*")
    parser.add_argument("number", type=str)
    parser.add_argument("--capitalize", default=False, action="store_true")
    args = parser.parse_args()

    converted_text = nt.convert(args.number)
    if args.capitalize:
        text = converted_text.capitalize()
    else:
        text = converted_text

    print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
