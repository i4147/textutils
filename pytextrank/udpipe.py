import spacy
import spacy_udpipe
import pytextrank


spacy_udpipe.download("en")

text = "Compatibility of systems of linear constraints over the set of natural numbers. Criteria of compatibility of a system of linear Diophantine equations, strict inequations, and nonstrict inequations are considered. Upper bounds for components of a minimal set of solutions and algorithms of construction of minimal generating sets of solutions for all types of systems are given. These criteria and the corresponding algorithms for constructing a minimal supporting set of solutions can be used in solving all the considered types systems and systems of mixed types."

print("USING:", text)


nlp_udpipe = spacy_udpipe.load("en")
tr = pytextrank.TextRank(logger=None)
nlp_udpipe.add_pipe(tr.PipelineComponent, name="textrank", last=True)
doc_udpipe = nlp_udpipe(text)

print("keywords from udpipe processing:")

for phrase in doc_udpipe._.phrases:
    print("{:.4f} {:5d}  {}".format(phrase.rank, phrase.count, phrase.text))
    print(phrase.chunks)


nlp_spacy = spacy.load("en_core_web_sm")
tr2 = pytextrank.TextRank(logger=None)
nlp_spacy.add_pipe(tr2.PipelineComponent, name="textrank", last=True)
doc_spacy = nlp_spacy(text)

print("keywords from spacy processing:")

for phrase in doc_spacy._.phrases:
    print("{:.4f} {:5d}  {}".format(phrase.rank, phrase.count, phrase.text))
    print(phrase.chunks)
