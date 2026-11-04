import argparse
import codecs
import sys

from latextomd import __version__, latextomd

parser = argparse.ArgumentParser(description="""Basic usage: latextomd -i input.tex -o output.md""")
parser.add_argument("-v", default=False, help="show version and exit", action="store_true")
parser.add_argument("-i", help="input file path. Must be a .tex file")
parser.add_argument("-o", help="output file path (optionnal). By default the input file path with .md")
parser.add_argument(
    "--pandoc-enumerate",
    action="store_true",
    help="let pandoc handle enumerate environnements",
)
parser.add_argument("-d", action="store_true", help="debug mode")

args = parser.parse_args()

if args.v:
    print(f"This is latextomd version {__version__}")
    sys.exit(2)


def predict_encoding(file_path, n_lines=20):
    import chardet

    with open(file_path, "rb") as f:
        rawdata = b"".join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)["encoding"]


def main():
    options = {
        "pandoc_enumerate": args.pandoc_enumerate,
    }

    if not args.i:
        print("An input file must be specified.")
        sys.exit(2)
    source_file = args.i
    if not args.o:
        export_file = source_file.replace(".tex", ".md")
    else:
        export_file = args.o
    print("Source encoding:", predict_encoding(source_file))
    with codecs.open(source_file, "r", "utf-8") as f:
        latex_string = f.read()
        latextomd_object = latextomd.LatexToMd(latex_string, export_file, options)
        markdown_string = latextomd.to_markdown(latex_string, export_file)
        with codecs.open(export_file, "w", "utf-8") as f_out:
            f_out.write(markdown_string)


if __name__ == "__main__":
    main()
