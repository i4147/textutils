import json
import sys

import docopt
import fasttext


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    input_path = args["<input>"]

    params = {}
    for key_value in args["--param"]:
        key, value_str = key_value.split("=", 1)
        value = json.loads(value_str)
        params[key] = value

    if args["--output"] == "<stdout>":
        output = sys.stdout
    else:
        output = open(args["--output"], "w")
    qt_cutoff = int(args["--qt_cutoff"]) if args["--qt_cutoff"] is not None else 0
    learn_vectors(input_path, params, qt_cutoff, output)


def learn_vectors(input_path, params, qt_cutoff, output):
    model = fasttext.train_supervised(input_path, **params)
    model.quantize(input=input_path, cutoff=qt_cutoff, retrain=True, qnorm=True)

    dimensions = params.get("dim", 100)
    words = len(model.words)

    output.write("{0} {1}\n".format(words, dimensions))
    for word in model.get_words():
        vector = model.get_word_vector(word)
        output.write(" ".join([word] + [str(v) for v in vector]))
        output.write("\n")
