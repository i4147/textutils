import math
import random
from enum import Enum
from operator import itemgetter
from functools import singledispatch
from typing import List, Tuple, Dict, Optional
import numpy as np
from text_rank.graph import Graph, AdjacencyList, AdjacencyMatrix, Vertex


ConvergenceType = Enum("ConvergenceType", "ALL ANY")


def sum_edges(edges: Dict[str, float]) -> float:
    return sum(edges.values())


def accumulate_score(vertex: Vertex, ws: List[float], denom: List[float]):
    return math.fsum([weight / denom[edge] * ws[edge] for edge, weight in vertex.edges_in.items()])


@singledispatch
def text_rank_init(graph: Graph, uniform: bool = False, seed: Optional[int] = None) -> Tuple[List[float], List[float]]:
    raise NotImplementedError


@text_rank_init.register(AdjacencyList)
def text_rank_init_list(
    graph: AdjacencyList, uniform: bool = False, seed: Optional[int] = None
) -> Tuple[List[float], List[float]]:
    random.seed(seed)
    denom = [sum_edges(v.edges_out) for v in graph.vertices]
    denom = [d if d != 0.0 else 1.0 for d in denom]
    if uniform:
        ws = [1 / len(graph.vertices) for _ in graph.vertices]
    else:
        ws = [random.random() for _ in graph.vertices]
        norm = sum(ws)
        ws = [w / norm for w in ws]
    return ws, denom


@text_rank_init.register(AdjacencyMatrix)
def text_rank_init_matrix(
    graph: AdjacencyMatrix, uniform: bool = False, seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    random.seed(seed)
    if uniform:
        ws = np.ones(graph.vertex_count) / graph.vertex_count
    else:
        ws = np.array([random.random() for _ in range(graph.vertex_count)])
        ws = ws / np.sum(ws)
    denom = np.reshape(np.sum(graph.adjacency_matrix, axis=1), (-1, 1))
    denom[denom == 0.0] = 1.0
    return ws, denom


@singledispatch
def text_rank_update(graph: Graph, ws: List[float], denom: List[float], damping: float = 0.85) -> List[float]:
    raise NotImplementedError


@text_rank_update.register(AdjacencyList)
def text_rank_update_list(
    graph: AdjacencyList, ws: List[float], denom: List[float], damping: float = 0.85
) -> List[float]:
    updates = [accumulate_score(v, ws, denom) for v in graph.vertices]
    ws = [(1 - damping) + damping * update for update in updates]
    return ws


@text_rank_update.register(AdjacencyMatrix)
def text_rank_update_matrix(
    graph: AdjacencyMatrix, ws: np.ndarray, denom: np.ndarray, damping: float = 0.85
) -> np.ndarray:
    update = np.dot(ws, graph.adjacency_matrix / denom)
    ws = (1 - damping) + damping * update
    return ws


@singledispatch
def text_rank_output(graph: Graph, ws: List[float]) -> List[Tuple[str, float]]:
    raise NotImplementedError


@text_rank_output.register(AdjacencyList)
def text_rank_output_list(graph: AdjacencyList, ws: List[float]) -> List[Tuple[str, float]]:
    norm = sum(ws)
    ws = [w / norm for w in ws]
    return sorted(zip(map(lambda v: v.value, graph.vertices), ws), key=itemgetter(1), reverse=True)


@text_rank_output.register(AdjacencyMatrix)
def text_rank_output_matrix(graph: AdjacencyMatrix, ws: np.ndarray) -> List[Tuple[str, float]]:
    ws = ws / np.sum(ws)
    return sorted(zip(graph.label2idx.keys(), ws), key=itemgetter(1), reverse=True)


def text_rank(
    graph: Graph,
    damping: float = 0.85,
    convergence: float = 0.0001,
    convergence_type: ConvergenceType = ConvergenceType.ALL,
    niter: int = 200,
    uniform: bool = False,
    seed: Optional[int] = None,
) -> List[Tuple[str, float]]:
    if not 0 <= damping <= 1:
        raise ValueError(f"damping must be between `0` and `1`, got {damping}")
    converge = all if convergence_type is ConvergenceType.ALL else any

    ws_prev, denom = text_rank_init(graph, uniform=uniform, seed=seed)

    for _ in range(niter):
        ws = text_rank_update(graph, ws_prev, denom, damping)
        if converge(abs(p - c) < convergence for p, c in zip(ws_prev, ws)):
            break
        ws_prev = ws

    return text_rank_output(graph, ws)
