import logging
import re
from pathlib import Path
from typing import Pattern
import bioc
import docopt
import spacy
import tqdm
import yaml

from radtext.cmd.cmd_utils import process_options, process_file
from radtext.models.ner.ner_regex import NerRegExExtractor, BioCNerRegex, NerRegexPattern
from radtext.models.ner.ner_spacy import NerSpacyExtractor, BioCNerSpacy


from radtext.models.ner.radlex import RadLex4


def load_yml(pathname):
    def ner_compile(pattern_str: str) -> Pattern:
        pattern_str = re.sub(" ", r"\\s+", pattern_str)
        return re.compile(pattern_str, re.I | re.M)

    with open(pathname) as fp:
        phrases = yaml.load(fp, yaml.FullLoader)

    patterns = []
    for concept_id, (concept, v) in enumerate(phrases.items()):
        npattern = NerRegexPattern()
        npattern.concept_id = str(concept_id)
        npattern.concept = concept

        if "include" in v:
            npattern.include_patterns += [ner_compile(p) for p in v["include"]]
        else:
            raise ValueError("%s: No patterns" % concept)

        if "exclude" in v:
            npattern.exclude_patterns += [ner_compile(p) for p in v["exclude"]]

        patterns.append(npattern)
    logging.debug("%s: Loading %s phrases.", pathname, len(patterns))
    return patterns


def main():
    argv = docopt.docopt(__doc__)
    process_options(argv)

    try:
        if argv["spacy"]:
            nlp = spacy.load(argv["--spacy-model"], exclude=["ner", "parser", "senter"])
            radlex = RadLex4(argv["--radlex"])
            matchers = radlex.get_spacy_matchers(nlp)
            extractor = NerSpacyExtractor(nlp, matchers)
            processor = BioCNerSpacy(extractor, "RadLex")
        elif argv["regex"]:
            patterns = load_yml(argv["--phrases"])
            extractor = NerRegExExtractor(patterns)
            processor = BioCNerRegex(extractor, name=Path(argv["--phrases"]).stem)
        else:
            raise KeyError
    except KeyError as e:
        raise e

    process_file(argv["-i"], argv["-o"], processor, bioc.PASSAGE)


if __name__ == "__main__":
    main()
