import argparse
import sys

from metext import (
    analyse,
    list_decoders_names,
    list_extractors_names,
    list_printers_names,
    print_analysis_output,
)
from metext.__version__ import __version__
from metext.utils.fileinput import FileInputExtended

decoders = list_decoders_names(active_only=True)
extractors = list_extractors_names(active_only=True)
printers = list_printers_names(active_only=True)


def build_parser():
    main_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    main_parser.add_argument(
        "-i",
        "--input",
        action="append",
        help=(
            "File path to process. Wildcards can be used."
            " Reads from STDIN if no input files defined via arguments -i or -f."
            " If -f argument is used, the input file paths are extended with the list of paths from the file."
        ),
    )
    main_parser.add_argument(
        "-f",
        "--file",
        help="Read input file paths from a file. One file path per line.",
    )
    main_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Enables recursive wildcards (**) for -i and -f arguments.",
    )
    main_parser.add_argument(
        "-o",
        "--output",
        nargs=1,
        help="File to write the output to. Outputs to STDOUT if no file given.",
        default=["-"],
    )
    main_parser.add_argument(
        "-d",
        "--decode",
        nargs="*",
        help=("Select formats that should be tried for decoding from. If no format selected, all will be tried."),
        choices=decoders,
        default=decoders,
    )
    main_parser.add_argument(
        "-e",
        "--extract",
        nargs="*",
        help=(
            "Select patterns that should be extracted."
            " If no pattern is selected, all supported patterns will be searched."
        ),
        choices=extractors,
        default=extractors,
    )
    main_parser.add_argument(
        "-F",
        "--out-format",
        nargs=1,
        help="Select output format of found patterns.",
        choices=printers,
        default=["json"],
    )
    main_parser.add_argument("--version", action="version", version="%(prog)s v" + __version__)
    return main_parser


def unglob_filepaths(filepaths, recursive=False):
    import glob
    from os.path import abspath, isfile

    for path in filepaths or []:
        yield from (abspath(p) for p in glob.iglob(path, recursive=recursive) if isfile(p))


def read_filepaths(file, recursive=False):
    if not file:
        return
    with open(file, "r") as fp:
        yield from unglob_filepaths(fp.readlines(), recursive=recursive)


def main():
    parser = build_parser()
    args = parser.parse_args()
    input_files = list(
        set(unglob_filepaths(args.input, args.recursive)).union(set(read_filepaths(args.file, args.recursive)))
    )
    if not input_files and (args.input or args.file):
        sys.exit("No input files found")
    with FileInputExtended(input_files or ["-"], mode="rb") as f:
        res = analyse(f, [(dec, {}) for dec in args.decode], [(ex, {}) for ex in args.extract])
    print_analysis_output(res, filename=args.output[0], printer=args.out_format[0])


if __name__ == "__main__":
    main()
