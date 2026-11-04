from itertools import chain
from operator import itemgetter
from typing import Optional, Callable, Type, List, Dict, Set
from text_rank.utils import filter_pos, norm_token
from text_rank.text_rank import text_rank, ConvergenceType
from text_rank.graph import keyword_graph, AdjacencyMatrix, Graph


def join_adjacent_keywords(candidates: List[str], offsets: Dict[str, List[str]]) -> Set[str]:
    candidates = list(chain(*([(candidate, o) for o in offsets[candidate]] for candidate in candidates)))
    candidates = sorted(candidates, key=itemgetter(1))
    keywords = []
    current = []
    prev = None
    for kw, i in candidates:
        if not current or i == prev + 1:
            current.append(kw)
        else:
            keywords.append(" ".join(current))
            current = [kw]
        prev = i
    if current:
        keywords.append(" ".join(current))
    return set(keywords)


def keywords(
    tokens: List[Dict[str, str]],
    nwords: Optional[int] = None,
    winsz: int = 2,
    damping: float = 0.85,
    convergence: float = 0.0001,
    convergence_type: ConvergenceType = ConvergenceType.ANY,
    niter: int = 200,
    seed: Optional[int] = None,
    sim: Callable[..., float] = lambda x, y, **kwargs: 1,
    norm: Callable[[str], str] = norm_token,
    filt: Callable[[Dict[str, str]], bool] = filter_pos,
    GraphType: Type[Graph] = AdjacencyMatrix,
) -> Set[str]:
    graph, offsets = keyword_graph(tokens, winsz, sim, norm, filt, GraphType)
    if nwords is None:
        nwords = len(tokens) // 3
    keywords = text_rank(
        graph, damping=damping, convergence=convergence, convergence_type=convergence_type, niter=niter, seed=seed
    )[:nwords]
    keywords = join_adjacent_keywords([kw[0] for kw in keywords], offsets)
    return keywords
