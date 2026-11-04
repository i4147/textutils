from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Callable,
)

from networkx import (
    Graph,
    pagerank,
)

from .utils import (
    parse_text_into_sentences,
    build_sentence_graph,
)
from .sentence import Sentence


__all__: Tuple[str, ...] = ("TextRank",)


class TextRank:
    def __init__(self, tokenizer: Callable[[str], List[str]], tolerance: float = 0.05) -> None:
        self.tokenizer: Callable[[str], List[str]] = tokenizer
        self.tolerance: float = tolerance

    def summarize(self, text: str, num_sentences: int = 3, verbose: bool = True) -> Union[str, List[str]]:

        sentences: List[Sentence] = parse_text_into_sentences(text, self.tokenizer)

        graph: Graph = build_sentence_graph(sentences, tolerance=self.tolerance)

        pageranks: Dict[Sentence, float] = pagerank(graph, weight="weight")

        sentences = sorted(pageranks, key=pageranks.get, reverse=True)
        sentences = sentences[:num_sentences]
        sentences = sorted(sentences, key=lambda sentence: sentence.index)

        # return summaries
        summaries = [sentence.text for sentence in sentences]
        if verbose:
            return "\n".join(summaries)
        else:
            return summaries
