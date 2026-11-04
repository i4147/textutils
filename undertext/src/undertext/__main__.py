# -*- coding=utf-8 -*-

import argparse as ap
from . import __cli__ as cli, util


parser = ap.ArgumentParser(prog="undertext", formatter_class=ap.ArgumentDefaultsHelpFormatter)
parser.set_defaults(fn=parser.print_help)
subparsers = parser.add_subparsers()

read_parser = subparsers.add_parser("read", epilog="Note: Some optional arguments are hidden")
read_parser.set_defaults(fn=cli.cmd_read)
read_parser.add_argument("input_fp", metavar="input", help="input file")
read_parser.add_argument(
    "--fmt", type=str, default=ap.SUPPRESS, help="specify the format if it can't be guessed from the file extension"
)
read_parser.add_argument("--after", type=util.parse_time_any, help="show only captions that start after")
read_parser.add_argument("--before", type=util.parse_time_any, help="show only captions that end before")
read_parser.add_argument("--fps", type=float, default=ap.SUPPRESS, help=ap.SUPPRESS)

convert_parser = subparsers.add_parser(
    "convert", epilog="Note: Some optional arguments are hidden and need to be prefixed with '--input-' or '--output-'"
)
convert_parser.set_defaults(fn=cli.cmd_convert)
convert_parser.add_argument("input_fp", metavar="input", help="input file")
convert_parser.add_argument("output_fp", metavar="output", help="output file")
convert_parser.add_argument(
    "-o", "--overwrite", action=ap.BooleanOptionalAction, default=False, help="overwrite existing output file"
)

convert_parser.add_argument(
    "--input-fmt",
    type=str,
    default=ap.SUPPRESS,
    help="specify the input format if it can't be guessed from the file extension",
)
convert_parser.add_argument(
    "--output-fmt",
    type=str,
    default=ap.SUPPRESS,
    help="specify the output format if it can't be guessed from the file extension",
)

convert_parser.add_argument("--input-fps", type=float, default=ap.SUPPRESS, help=ap.SUPPRESS)
convert_parser.add_argument("--output-fps", type=float, default=ap.SUPPRESS, help=ap.SUPPRESS)


def main(args=None):
    arguments = vars(parser.parse_args(args))
    fn = arguments.pop("fn")
    return fn(**arguments)


if __name__ == "__main__":
    main()
