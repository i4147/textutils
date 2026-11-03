import argparse
from .main import main


def run() -> None:
    parser = argparse.ArgumentParser(
        description="Convert handwritten PDF notes to text. Output directories are derived from the PDF name."
    )
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    args = parser.parse_args()
    main(args.pdf_path)


if __name__ == "__main__":
    run()
