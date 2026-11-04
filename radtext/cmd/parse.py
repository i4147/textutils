import docopt
import bioc
from radtext.cmd.cmd_utils import process_options, process_file
from radtext.models.bllipparser import BioCParserBllip


def main():
    argv = docopt.docopt(__doc__)
    process_options(argv)
    processor = BioCParserBllip(model_dir=argv["--bllip-model"], only_ner=argv["--only-ner"])
    process_file(argv["-i"], argv["-o"], processor, bioc.DOCUMENT)


if __name__ == "__main__":
    main()
