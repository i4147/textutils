from typing import Optional, Callable, Type, List
from text_rank.utils import overlap, norm_sentence
from text_rank.text_rank import text_rank, ConvergenceType
from text_rank.graph import sentence_graph, AdjacencyMatrix, Graph


def summarize(
    sentences: List[str],
    nsents: Optional[int] = None,
    keep_order: bool = True,
    damping: float = 0.85,
    convergence: float = 0.0001,
    convergence_type: ConvergenceType = ConvergenceType.ALL,
    niter: int = 200,
    seed: Optional[int] = None,
    sim: Callable[..., float] = overlap,
    norm: Callable[[str], str] = norm_sentence,
    GraphType: Type[Graph] = AdjacencyMatrix,
) -> List[str]:
    graph, offsets = sentence_graph(sentences, sim, norm, GraphType)
    if nsents is None:
        nsents = len(sentences) // 3
    selected = text_rank(
        graph,
        damping=damping,
        convergence=convergence,
        convergence_type=convergence_type,
        niter=niter,
        seed=seed,
    )[:nsents]
    indices = [offsets[s[0]][0] for s in selected]
    if keep_order:
        return [sentences[i] for i in sorted(indices)]
    return [sentences[i] for i in indices]
