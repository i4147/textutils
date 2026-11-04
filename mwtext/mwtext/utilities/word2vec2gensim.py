import logging

import docopt
from gensim.models import KeyedVectors

logger = logging.getLogger(__name__)


def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    logging.basicConfig(
        level=logging.INFO if not args["--debug"] else logging.DEBUG,
        format="%(asctime)s %(levelname)s:%(name)s -- %(message)s",
    )

    input_path = args["<input>"]
    output_path = args["<output>"]
    limit = int(args["--limit"]) if args["--limit"] is not None else None
    verbose = args["--verbose"]

    word2vec2gensim(input_path, limit, output_path, verbose)


def word2vec2gensim(input_path, limit, output_path, verbose):
    model = KeyedVectors.load_word2vec_format(input_path, limit=limit)
    model.save(output_path)
