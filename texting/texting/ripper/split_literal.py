from functools import partial

from texting.enum.regexes import LITERAL
from texting.ripper.ripper import ripper

split_literal = partial(ripper, LITERAL)
