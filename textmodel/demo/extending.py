# -*- coding: latin-1 -*-


import sys

sys.path.insert(0, "..")

from textmodel import TextModel
from textmodel.texeltree import Characters
from textmodel.container import Container


class Fraction(Container):
    def __init__(self, denominator, nominator, **kwds):
        self.denominator = denominator
        self.nominator = nominator
        Container.__init__(self, **kwds)

    def get_content(self):
        return self.denominator, self.nominator

    def get_emptychars(self):
        return "(;)"


class Root(Container):
    def __init__(self, content, **kwds):
        self.content = content
        Container.__init__(self, **kwds)

    def get_content(self):
        return [self.content]


def mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model


frac = Fraction(Characters("3"), Characters("4"))
root = Root(Characters("2"))

text = TextModel("A text which contains some math\n\n")
text.append("f = ")
text.append(mk_textmodel(frac))
text.append("\n\n")
text.append(mk_textmodel(root))
text.append(" = 1.414214 ...")
text.texel.dump()
