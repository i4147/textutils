# -*- coding: utf-8 -*-

import pytextrank
import spacy
import en_core_web_sm

nlp = en_core_web_sm.load()
nlp.add_pipe("textrank", last=True)
# nlp = spacy.load("en_core_web_sm")
# nlp.add_pipe("textrank")

txt = """To return to my trees. This, as you know, is something that I do often. But sometimes, I even surprise myself with how powerful the pull of trees can be. Take this latest tree. I walked out onto this huge expanse of hard sand and then headed directly across to where there was this amazing old fir tree whose growth seems to have split the sandstone, its top is blown off, and its roots getting salted with every winter storm. I could not easily capture its grandness in one image so I pieced a few together and relied mostly on a short video for painting references. After all the little plein air paintings, this is my first studio painting from Hornby Island. Well, let’s see what we have shall we?"""

doc = nlp(txt)

data = [(txt, {"doc_id": i}) for i in range(5)]


for doc, context in nlp.pipe(data, as_tuples=True, n_process=-1):
    out = {"doc_id": context["doc_id"], "keyphrases": [(phr.text, phr.rank) for phr in doc._.phrases]}
    print(out)
