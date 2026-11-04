# -*- coding: utf-8 -*-


import logging
import math
import string
import warnings
from itertools import repeat
from multiprocessing import Pool
from types import LambdaType
from typing import List, Optional, Tuple, Callable, Set, Generator, Dict, Union

import networkx
import networkx as nx

from jgtextrank.metrics import TermGraphValue, GCValue, _gaussian_normalise, _log_normalise, _term_size_normalize
from jgtextrank.preprocessing.normaliser import normalize
from jgtextrank.preprocessing.segmentation import pos_tagging, word_2_tokenised_sentences
from jgtextrank.utility import (
    avg_dicts,
    CorpusContent2RawSentences,
    get_top_n_from_dict,
    flatten,
    is_list_of_list,
    sort_dict_by_value,
    export_list_of_tuple_into_csv,
    export_list_of_tuples_into_json,
)

__author__ = "Jie Gao <j.gao@sheffield.ac.uk>"

__all__ = [
    "Vertex",
    "preprocessing",
    "preprocessing_tokenised_context",
    "_pos_tagging_tokenised_corpus_context",
    "_syntactic_filter",
    "_syntactic_filter_context",
    "_is_multiple_context",
    "_get_cooccurs",
    "_get_cooccurs_from_single_context",
    "_build_vertices_representations",
    "_compute_vertex",
    "build_cooccurrence_graph",
    "_draw_edges",
    "_is_top_t_vertices_connection",
    "_reweight_filtered_terms",
    "_term_size_normalize",
    "_log_normalise",
    "_gaussian_normalise",
    "_keywords_extraction_from_preprocessed_context",
    "_collapse_adjacent_keywords",
    "_load_preprocessed_corpus_context",
    "keywords_extraction",
    "keywords_extraction_from_segmented_corpus",
    "keywords_extraction_from_tagged_corpus",
    "keywords_extraction_from_corpus_directory",
    "compute_TeRGraph",
    "compute_neighborhood_size",
]

_logger = logging.getLogger("jgtextrank.core")


MAX_PROCESSES = 1

pos_tag = pos_tagging()

noun_adjective_filter = lambda t: filter(lambda a: a[1] == "NNS" or a[1] == "NNP" or a[1] == "NN" or a[1] == "JJ", t)


class Vertex(object):
    def __init__(self, word, word_type, tag=None):
        self.word = word
        self.word_type = word_type
        self.tag = tag
        self.score = -1
        self.co_occurs = []
        self.context = []

    def __str__(self):
        return (
            "vertex word: '"
            + self.word
            + "', word type (normed): '"
            + self.word_type
            + "'"
            + ", co-occur vertices: "
            + str(self.co_occurs)
        )

    def __repr__(self):
        return str(self)


def preprocessing(
    text: str,
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Optional[Set[str]] = None,
    lemma: bool = False,
) -> Generator[Tuple[List[str], List[Tuple[str, str]]], None, None]:

    tokenised_sentences = word_2_tokenised_sentences(text)

    return preprocessing_tokenised_context(
        tokenised_sentences, syntactic_categories=syntactic_categories, stop_words=stop_words, lemma=lemma
    )


def preprocessing_tokenised_context(
    tokenised_context: Union[Generator[List[str], None, None], List[List[str]]],
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Optional[Set[str]] = None,
    lemma: bool = False,
) -> Generator[Tuple[List[str], List[Tuple[str, str]]], None, None]:
    _check_required_values(False, syntactic_categories)

    pos_filter = lambda t: filter(lambda a: a[1] in syntactic_categories, t)
    stop_words_filter = None if stop_words is None else lambda t: filter(lambda a: a[0] not in stop_words, t)

    tagged_tokenised_context_collection = _pos_tagging_tokenised_corpus_context(tokenised_context, lemma=lemma)

    for tokenised_context, pos_tagged_context in tagged_tokenised_context_collection:
        yield (
            tokenised_context,
            _syntactic_filter_context(pos_tagged_context, pos_filter=pos_filter, stop_words_filter=stop_words_filter),
        )


def _pos_tagging_tokenised_corpus_context(
    tokenised_corpus_context: Generator[List[str], None, None], lemma: bool = False
) -> Generator[Tuple[List[str], List[Tuple[str, str]]], None, None]:
    for tokenised_sentence in tokenised_corpus_context:
        sentence_token_list = list(tokenised_sentence)
        tagged_sentence_token_list = pos_tag(sentence_token_list)

        sentence_token_list, normed_tagged_sentence_token_list = _normalise_tagged_token_list(
            tagged_sentence_token_list, lemma=lemma
        )

        yield (sentence_token_list, normed_tagged_sentence_token_list)


def _normalise_tagged_token_list(
    tagged_token_list: List[Tuple[str, str]], lemma: bool = False
) -> Tuple[List[str], List[Tuple[str, str]]]:

    normed_tagged_token_list = [
        (normalize(tagged_token[0], lemma=lemma, pos_tag=tagged_token[1]), tagged_token[1])
        for tagged_token in tagged_token_list
    ]
    normed_token_list = [norm_token[0] for norm_token in normed_tagged_token_list]
    return normed_token_list, normed_tagged_token_list


def _syntactic_filter(
    pos_tagged_tokenised_sents: List[List[Tuple[str, str]]],
    pos_filter: Optional[Union[Callable[[List[Tuple[str, str]]], Tuple[str, str]], LambdaType]] = None,
    stop_words_filter: Optional[Union[Callable[[Tuple[str, str]], Tuple[str, str]], LambdaType]] = None,
) -> Generator[List[Tuple[str, str]], None, None]:
    _logger.info("syntactic filtering ...")
    # print("pos_tagged_tokenised_sents: ", list(pos_tagged_tokenised_sents))
    if not is_list_of_list(pos_tagged_tokenised_sents):
        raise Exception(
            "Incorrected format. Expect: a list of textual context token list. "
            "Example: [[(token, pos_tag), ...], [(token, pos_tag), ...], ...]"
        )

    for pos_tagged_tokenised_sent in pos_tagged_tokenised_sents:
        # print("pos_tagged_tokenised_sent: ", pos_tagged_tokenised_sent)
        yield _syntactic_filter_context(pos_tagged_tokenised_sent, pos_filter, stop_words_filter)


def _syntactic_filter_context(
    pos_tagged_tokens: List[Tuple[str, str]],
    pos_filter: Optional[Union[Callable[[List[Tuple[str, str]]], Tuple[str, str]], LambdaType]] = None,
    stop_words_filter: Optional[Union[Callable[[List[Tuple[str, str]]], Tuple[str, str]], LambdaType]] = None,
    punc_filter: Union[Callable[[List[Tuple[str, str]]], Tuple[str, str]], LambdaType] = lambda t: filter(
        lambda a: a[0] not in string.punctuation, t
    ),
) -> List[Tuple[str, str]]:

    if pos_filter is None:
        pos_filter = noun_adjective_filter

    filtered_context = pos_filter(pos_tagged_tokens)

    if stop_words_filter:
        pos_filtered_context = list(filtered_context)
        # print("pos_filtered_context: ", pos_filtered_context)
        filtered_context = stop_words_filter(pos_filtered_context)

    final_filtered_context = list(punc_filter(filtered_context))
    # print("final_filtered_context: ", final_filtered_context)
    return final_filtered_context


def _is_multiple_context(corpus_context):
    return is_list_of_list(corpus_context)


def _get_cooccurs(
    syntactic_unit: str,
    vertices_cooccur_context_corpus: List[List[str]],
    all_filtered_context_tokens: Optional[List[str]] = None,
    window_size: int = 2,
) -> Set[str]:

    all_cooccurs = []

    if _is_multiple_context(vertices_cooccur_context_corpus):
        for filtered_corpus_context in vertices_cooccur_context_corpus:
            all_cooccurs.append(_get_cooccurs_from_single_context(syntactic_unit, filtered_corpus_context, window_size))
    else:
        all_cooccurs = _get_cooccurs_from_single_context(syntactic_unit, vertices_cooccur_context_corpus, window_size)

    flatten_all_cooccurs = flatten(all_cooccurs)

    if all_filtered_context_tokens:
        cooccur_filter = lambda t: filter(lambda a: a in all_filtered_context_tokens, t)
        flatten_all_cooccurs = cooccur_filter(flatten_all_cooccurs)

    return set(flatten_all_cooccurs)


def _get_cooccurs_from_single_context(
    syntactic_unit: str, tokenised_context: Union[List[List[str]], List[str]], window_size: int = 2
) -> List[str]:
    if syntactic_unit not in tokenised_context:
        return []

    # current_index = tokenised_context.index(syntactic_unit)
    all_indices = [i for i, x in enumerate(tokenised_context) if x == syntactic_unit]

    candidate_cooccurs = []
    current_index: int = 0
    for current_index in all_indices:
        context_size = len(tokenised_context)

        forward_context = [
            (current_index - forward - 1)
            for forward in range(window_size)
            if (current_index - forward - 1) >= 0
            and (current_index - forward - 1) <= context_size - 1
            and (current_index - forward - 1) < current_index
        ]

        backward_context = [
            (current_index + backward + 1)
            for backward in range(window_size)
            if (current_index + backward + 1) >= 0
            and (current_index + backward + 1) <= context_size - 1
            and (current_index + backward + 1) > current_index
        ]

        cooccur_context = forward_context + backward_context

        candidate_cooccurs.append([tokenised_context[cooccur_word_index] for cooccur_word_index in cooccur_context])

    return flatten(candidate_cooccurs)


def _build_vertices_representations(
    all_tokenised_filtered_context: Union[List[List[str]], List[str]],
    all_tokenised_context: Optional[List[List[str]]] = None,
    conn_with_original_ctx: bool = True,
    window_size: int = 2,
) -> List[Vertex]:
    _logger.info("computing vertices representations...")
    vertices = list()

    all_filtered_context_tokens = set([context_token for context_token in flatten(all_tokenised_filtered_context)])

    if conn_with_original_ctx:
        vertices_coccur_context = all_tokenised_context
    else:
        vertices_coccur_context = all_tokenised_filtered_context

    # print("_build_vertices_representations >> all_tokenised_filtered_context: ", all_tokenised_filtered_context)

    global MAX_PROCESSES
    with Pool(processes=MAX_PROCESSES) as pool:
        vertices = pool.starmap(
            _compute_vertex,
            zip(
                all_filtered_context_tokens,
                repeat(vertices_coccur_context),
                repeat(all_filtered_context_tokens),
                repeat(window_size),
            ),
        )

    _logger.info("total size of vertices: %s", len(vertices))
    # print("all vertices: ", vertices)
    return vertices


def _compute_vertex(
    syntactic_unit: str,
    vertices_cooccur_context_corpus: List[List[str]],
    all_filtered_context_tokens: Optional[List[str]] = None,
    window_size: int = 2,
):
    _logger.debug("compute vertex [%s] ...", syntactic_unit)

    vertex = Vertex(syntactic_unit, syntactic_unit)

    # print("filtered_context_list in _compute_vertex : ", filtered_context_list)
    cooccured_syntactic_units = _get_cooccurs(
        syntactic_unit, vertices_cooccur_context_corpus, all_filtered_context_tokens, window_size
    )
    # print(syntactic_unit, ", cooccured_syntactic_units: ", cooccured_syntactic_units)
    vertex.co_occurs = [syntactic_unit for syntactic_unit in cooccured_syntactic_units]
    _logger.debug("Done.")
    return vertex


def build_cooccurrence_graph(
    preprocessed_context: Generator[Tuple[List[str], List[Tuple[str, str]]], None, None],
    directed: bool = False,
    weighted: bool = False,
    conn_with_original_ctx=True,
    window: int = 2,
) -> Tuple[Union[networkx.DiGraph, networkx.Graph], List[List[str]]]:
    all_tokenised_context = []
    all_tokenised_filtered_context = []
    for tokenised_context, context_syntactic_units in preprocessed_context:
        all_tokenised_context.append(tokenised_context)
        all_tokenised_filtered_context.append([
            context_syntactic_unit[0] for context_syntactic_unit in context_syntactic_units
        ])

    vertices = _build_vertices_representations(
        all_tokenised_filtered_context,
        all_tokenised_context=all_tokenised_context,
        conn_with_original_ctx=conn_with_original_ctx,
        window_size=window,
    )

    cooccurence_graph = nx.Graph()

    cooccurence_graph.add_nodes_from([vertex.word_type for vertex in vertices], weight=1.0)
    cooccurence_graph.add_weighted_edges_from(_draw_edges(vertices))

    if directed:
        return cooccurence_graph.to_directed(), all_tokenised_context
    else:
        return cooccurence_graph.to_undirected(), all_tokenised_context


def _draw_edges(vertices, weight=1.0) -> List[Tuple[str, str, float]]:
    # print([(vertex.word_type,vertex.co_occurs) for vertex in vertices])

    edges = []
    for vertex in vertices:
        for co_occur in vertex.co_occurs:
            edges.append((vertex.word_type, co_occur, weight))
    return edges


def _is_top_t_vertices_connection(collapsed_term, top_t_vertices) -> bool:
    return any(top_t_vertex[0] in collapsed_term for top_t_vertex in top_t_vertices)


def _reweight_filtered_terms(
    collapsed_terms, top_t_vertices, all_vertices, weight_comb="norm_max", mu=5
) -> Dict[str, float]:
    _logger.info("MWTs weighing ...")
    weighted_terms = dict()

    global MAX_PROCESSES

    if weight_comb == "gcvalue":
        tg_cvalue = GCValue(weight_comb=weight_comb, mu=mu, parallel_workers=MAX_PROCESSES)
        weighted_terms = tg_cvalue.weighing(collapsed_terms, all_vertices, top_t_vertices)
    else:
        tg_value = TermGraphValue(weight_comb=weight_comb, mu=mu, parallel_workers=MAX_PROCESSES)
        weighted_terms = tg_value.weighing(collapsed_terms, all_vertices, top_t_vertices)

    _logger.info("done.")
    return weighted_terms


def _weight_nodes_with_centrality_metrics(scoring_method, cooccurrence_graph) -> Dict[str, float]:
    if nx.is_connected(cooccurrence_graph):
        weighted_nodes = scoring_method(cooccurrence_graph)
    else:
        warnings.warn("Graph is not (strongly) connected. Nodes will be measured in connected subgraphs.")
        weighted_nodes = {}
        for c in nx.connected_components(cooccurrence_graph):
            connected_graph = cooccurrence_graph.subgraph(c)
            try:
                weighted_nodes.update(scoring_method(connected_graph))
            except ZeroDivisionError:
                continue

    weighted_nodes = {k: v for k, v in weighted_nodes.items() if v != float("inf")}
    return weighted_nodes


def compute_TeRGraph(term_graph: networkx.Graph) -> Dict[str, float]:
    all_nodes = term_graph.nodes()
    node_weights = dict()

    _logger.debug("total nodes: %s", len(all_nodes))

    total_isolated_nodes = 0
    for node in all_nodes:
        list_of_neighbors = list(term_graph.neighbors(node))
        n_a = len(list_of_neighbors)
        if n_a == 0:
            total_isolated_nodes += 1

        # print("---> list_of_neighbors: ", list_of_neighbors)
        n_t_i = (
            0
            if n_a == 0
            else sum([len(list(term_graph.neighbors(neighbor_node))) for neighbor_node in list_of_neighbors])
        )
        # print("total number of neighbors of neighbors: ", n_t_i)
        node_weight = 0 if n_a == 0 else math.log2(1.5 + 1 / (n_a + n_t_i))
        node_weights[node] = node_weight

    _logger.debug("total isolated nodes: %s", total_isolated_nodes)
    _logger.debug("total weighted nodes: %s", len(node_weights))
    return node_weights


def compute_neighborhood_size(term_cooccur_graph) -> Dict[str, int]:
    node_weights = dict()
    num_of_selfloops = nx.number_of_selfloops(term_cooccur_graph)
    if num_of_selfloops > 0:
        _logger.warning("remove %s selfloops.", num_of_selfloops)
        term_cooccur_graph.remove_edges_from(nx.selfloop_edges(term_cooccur_graph))

    all_nodes = term_cooccur_graph.nodes()
    for node in all_nodes:
        neighbors = nx.all_neighbors(term_cooccur_graph, node)
        node_weights[node] = len(list(neighbors))

    return node_weights


def _keywords_extraction_from_preprocessed_context(
    preprocessed_corpus_context: Union[
        Generator[Tuple[List[str], List[Tuple[str, str]]], None, None], List[Tuple[List[str], List[Tuple[str, str]]]]
    ],
    top_p: float = 0.3,
    top_t: Optional[int] = None,
    window: Optional[int] = 2,
    directed: bool = False,
    weighted: bool = False,
    conn_with_original_ctx: bool = True,
    max_iter: int = 100,
    tol: float = 1.0e-6,
    solver: str = "pagerank",
    weight_comb: str = "norm_max",
    mu: int = 5,
) -> Tuple[Dict[str, float], List[Tuple[str, float]]]:
    cooccurrence_graph, original_tokenised_context = build_cooccurrence_graph(
        preprocessed_corpus_context,
        directed=directed,
        weighted=weighted,
        conn_with_original_ctx=conn_with_original_ctx,
        window=window,
    )

    if solver == "pagerank":
        weighted_nodes = nx.pagerank(cooccurrence_graph, weight="weight", max_iter=max_iter, tol=tol)
    elif solver == "pagerank_numpy":
        weighted_nodes = nx.pagerank_numpy(cooccurrence_graph)
    elif solver == "pagerank_scipy":
        weighted_nodes = nx.pagerank_scipy(cooccurrence_graph, max_iter=max_iter, tol=tol)
    elif solver == "betweenness_centrality":
        weighted_nodes = nx.betweenness_centrality(cooccurrence_graph)
    elif solver == "edge_betweenness_centrality":
        weighted_nodes = nx.edge_betweenness_centrality(cooccurrence_graph)
        weighted_nodes = _flatten_nodes_betweenness_weights(weighted_nodes)
    elif solver == "degree_centrality":
        weighted_nodes = nx.degree_centrality(cooccurrence_graph)
    elif solver == "closeness_centrality":
        weighted_nodes = nx.closeness_centrality(cooccurrence_graph)
    elif solver == "hits":
        hits_values = nx.hits(cooccurrence_graph, max_iter=max_iter, tol=tol)
        hub_nodes = hits_values[0]
        authorities_nodes = hits_values[1]
        weighted_nodes = avg_dicts(hub_nodes, authorities_nodes)
    elif solver == "eigenvector_centrality":
        weighted_nodes = nx.eigenvector_centrality(cooccurrence_graph, max_iter=max_iter, tol=tol)
    elif solver == "katz_centrality":
        #  max_iter=max_iter, tol=tol
        weighted_nodes = nx.katz_centrality_numpy(cooccurrence_graph)
    elif solver == "communicability_betweenness":
        weighted_nodes = _weight_nodes_with_centrality_metrics(
            nx.communicability_betweenness_centrality, cooccurrence_graph
        )
    elif solver == "current_flow_closeness":
        weighted_nodes = _weight_nodes_with_centrality_metrics(nx.current_flow_closeness_centrality, cooccurrence_graph)
    elif solver == "current_flow_betweenness":
        weighted_nodes = _weight_nodes_with_centrality_metrics(
            nx.current_flow_betweenness_centrality, cooccurrence_graph
        )
    elif solver == "edge_current_flow_betweenness":
        weighted_nodes = _weight_nodes_with_centrality_metrics(
            nx.edge_current_flow_betweenness_centrality, cooccurrence_graph
        )
        weighted_nodes = _flatten_nodes_betweenness_weights(weighted_nodes)
    elif solver == "load_centrality":
        weighted_nodes = nx.load_centrality(cooccurrence_graph)
    elif solver == "clustering_coefficient":
        weighted_nodes = nx.clustering(cooccurrence_graph)
    elif solver == "TeRGraph":
        weighted_nodes = compute_TeRGraph(cooccurrence_graph)
    elif solver == "coreness":
        cooccurrence_graph.remove_edges_from(nx.selfloop_edges(cooccurrence_graph))
        weighted_nodes = nx.core_number(cooccurrence_graph)
    elif solver == "neighborhood_size":
        weighted_nodes = compute_neighborhood_size(cooccurrence_graph)
    else:
        ValueError(
            "The node weighting solver supports only pagerank, "
            "pagerank_numpy, pagerank_scipy, betweenness_centrality, "
            "edge_betweenness_centrality, degree_centrality, closeness_centrality, hits, "
            "eigenvector_centrality, katz_centrality, communicability_betweenness, "
            "current_flow_closeness, current_flow_betweenness, edge_current_flow_betweenness, "
            "load_centrality,clustering_coefficient,TeRGraph,coreness,neighborhood_size got '%s'" % solver
        )

    if top_t is None:
        top_t = round(len(weighted_nodes) * top_p)

    top_t_vertices = get_top_n_from_dict(weighted_nodes, top_t)

    _logger.debug("top T(t=%s) vertices: %s ...", top_t, top_t_vertices[:10])
    collapsed_terms = _collapse_adjacent_keywords(weighted_nodes, flatten(original_tokenised_context))

    weighted_terms = _reweight_filtered_terms(
        collapsed_terms, top_t_vertices, weighted_nodes, weight_comb=weight_comb, mu=mu
    )

    return weighted_terms, top_t_vertices


def _flatten_nodes_betweenness_weights(weighted_nodes):
    max_edge_dict = {}
    for edge_tuple, value in weighted_nodes.items():
        edge_node_1 = edge_tuple[0]
        edge_node_2 = edge_tuple[1]
        if edge_node_1 not in max_edge_dict or (edge_node_1 in max_edge_dict and max_edge_dict[edge_node_1] < value):
            max_edge_dict[edge_node_1] = value

        if edge_node_2 not in max_edge_dict or (edge_node_2 in max_edge_dict and max_edge_dict[edge_node_2] < value):
            max_edge_dict[edge_node_2] = value
    weighted_nodes = max_edge_dict
    return weighted_nodes


def _collapse_adjacent_keywords(weighted_keywords, original_tokenised_text):
    _logger.info("collapse adjacent keywords ...")

    keywords_tmp = [word for word, weight in weighted_keywords.items()]

    # normalised_tokenised_context = [token for token in original_tokenised_text]

    keyword_tag = "k"
    mark_keyword = lambda token, keyword_dict: keyword_tag if token in keywords_tmp else ""
    marked_text_tokens = [(token, mark_keyword(token, keywords_tmp)) for token in original_tokenised_text]

    # print("keywords marked text", marked_text_tokens)

    _key_terms = list()
    _current_term_units = []
    for marked_token in marked_text_tokens:
        if marked_token[1] == "k":
            _current_term_units.append(marked_token[0])
        else:
            if _current_term_units:
                _key_terms.append(_current_term_units)
            _current_term_units = []

    _logger.info("done.")
    return _key_terms


def _check_required_values(weighted, syntactic_categories):
    if weighted:
        _logger.warning("Weighted graph is not supported yet.")

    if syntactic_categories is None:
        raise ValueError("`syntactic_categories` cannot be None!")


def keywords_extraction(
    text: str,
    window: int = 2,
    top_p: float = 1,
    top_t: Optional[int] = None,
    directed: bool = False,
    weighted: bool = False,
    conn_with_original_ctx: bool = True,
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Set[str] = None,
    lemma: bool = False,
    solver: str = "pagerank",
    max_iter: int = 100,
    tol: float = 1.0e-6,
    weight_comb: str = "norm_max",
    mu: int = 5,
    workers: int = 1,
):
    _check_solver_option(solver)

    if (
        solver
        in [
            "communicability_betweenness",
            "current_flow_closeness",
            "current_flow_betweenness",
            "edge_current_flow_betweenness",
        ]
        and window < 5
    ):
        _logger.warning(
            "'%s' requires highly connected graph. "
            "Please consider to increase context window size. "
            "Isolated nodes would be removed by most of centrality "
            "and betweeness metrics otherwise. ",
            solver,
        )

    _check_required_values(weighted, syntactic_categories)
    _check_weight_comb_option(weight_comb)

    global MAX_PROCESSES
    MAX_PROCESSES = workers

    _logger.info(
        "pre-processing text with syntactic_categories [%s] and stop words [%s] ... ", syntactic_categories, stop_words
    )

    preprocessed_corpus_context = preprocessing(
        text, syntactic_categories=syntactic_categories, stop_words=stop_words, lemma=lemma
    )

    weighted_keywords, top_t_vertices = _keywords_extraction_from_preprocessed_context(
        preprocessed_corpus_context,
        window=window,
        top_p=top_p,
        top_t=top_t,
        directed=directed,
        weighted=weighted,
        conn_with_original_ctx=conn_with_original_ctx,
        solver=solver,
        max_iter=max_iter,
        tol=tol,
        weight_comb=weight_comb,
        mu=mu,
    )

    return list(sort_dict_by_value(weighted_keywords).items()), top_t_vertices


def _check_solver_option(solver):
    if solver not in [
        "pagerank",
        "pagerank_numpy",
        "pagerank_scipy",
        "betweenness_centrality",
        "degree_centrality",
        "hits",
        "closeness_centrality",
        "edge_betweenness_centrality",
        "eigenvector_centrality",
        "katz_centrality",
        "communicability_betweenness",
        "current_flow_closeness",
        "current_flow_betweenness",
        "edge_current_flow_betweenness",
        "load_centrality",
        "clustering_coefficient",
        "TeRGraph",
        "coreness",
        "neighborhood_size",
    ]:
        raise ValueError(
            "PageRank solver supports only 'pagerank', "
            "'pagerank_numpy', 'pagerank_scipy', 'betweenness_centrality', "
            "'edge_betweenness_centrality', 'degree_centrality', "
            "'closeness_centrality', 'hits', 'eigenvector_centrality', 'katz_centrality', "
            "'communicability_betweenness','current_flow_closeness',"
            " 'current_flow_betweenness', 'edge_current_flow_betweenness', 'load_centrality', "
            "'clustering_coefficient','TeRGraph','coreness','neighborhood_size' got '%s'" % solver
        )
    if solver == "pagerank_numpy" or solver == "katz_centrality":
        import pkg_resources

        pkg_resources.require("numpy")

    if solver == "pagerank_scipy":
        import pkg_resources

        pkg_resources.require("scipy")


def keywords_extraction_from_segmented_corpus(
    segmented_corpus_context: Union[Generator[List[str], None, None], CorpusContent2RawSentences],
    solver: str = "pagerank",
    max_iter: int = 100,
    tol: float = 1.0e-6,
    window: int = 2,
    top_p: float = 0.3,
    top_t: Optional[int] = None,
    directed: bool = False,
    weighted: bool = False,
    conn_with_original_ctx: bool = True,
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Set[str] = None,
    lemma: bool = False,
    weight_comb: str = "norm_max",
    mu: int = 5,
    export: bool = False,
    export_format: str = "csv",
    export_path: str = "",
    encoding: str = "utf-8",
    workers: int = 1,
) -> Tuple[List[Tuple[str, float]], Dict[str, float]]:
    global MAX_PROCESSES
    MAX_PROCESSES = workers

    _check_required_values(weighted, syntactic_categories)
    _check_export_option(export, export_format)
    _check_weight_comb_option(weight_comb)

    pre_processed_tokenised_context = preprocessing_tokenised_context(
        segmented_corpus_context, syntactic_categories=syntactic_categories, stop_words=stop_words, lemma=lemma
    )

    weighted_keywords, top_t_vertices = _keywords_extraction_from_preprocessed_context(
        pre_processed_tokenised_context,
        solver=solver,
        max_iter=max_iter,
        tol=tol,
        top_p=top_p,
        top_t=top_t,
        directed=directed,
        window=window,
        weighted=weighted,
        conn_with_original_ctx=conn_with_original_ctx,
        weight_comb=weight_comb,
        mu=mu,
    )

    sorted_weighted_keywords = list(sort_dict_by_value(weighted_keywords).items())

    _export_result(
        sorted_weighted_keywords, export=export, export_format=export_format, export_path=export_path, encoding=encoding
    )

    return sorted_weighted_keywords, top_t_vertices


def _export_result(weighted_term_results, export=False, export_format="csv", export_path="", encoding="utf-8"):
    if export:
        _logger.info("exporting sorted keywords into [%s]", export_path)
        if export_format.lower() == "csv":
            export_list_of_tuple_into_csv(export_path, weighted_term_results, header=["term", "weight"])
        else:
            export_list_of_tuples_into_json(export_path, weighted_term_results, encoding=encoding)

        _logger.info("complete result export.")


def _load_preprocessed_corpus_context(
    tagged_corpus_context: Union[List[List[Tuple[str, str]]], Generator[List[Tuple[str, str]], None, None]],
    pos_filter: Union[Callable[[List[Tuple[str, str]]], Tuple[str, str]], LambdaType] = None,
    stop_words_filter: Optional[Callable[[List[Tuple[str, str]]], Tuple[str, str]]] = None,
    lemma=False,
) -> Generator[Tuple[List[str], List[Tuple[str, str]]], None, None]:
    for tagged_context in tagged_corpus_context:
        normed_token_list, normed_tagged_context = _normalise_tagged_token_list(tagged_context, lemma=lemma)
        yield normed_token_list, _syntactic_filter_context(normed_tagged_context, pos_filter, stop_words_filter)


def keywords_extraction_from_tagged_corpus(
    tagged_corpus_context: List[List[Tuple[str, str]]],
    solver: str = "pagerank",
    max_iter: int = 100,
    tol: float = 1.0e-6,
    window: int = 2,
    top_p: float = 0.3,
    top_t: Optional[int] = None,
    directed: bool = False,
    weighted: bool = False,
    conn_with_original_ctx: bool = True,
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Set[str] = None,
    lemma: bool = False,
    weight_comb: str = "norm_max",
    mu: int = 5,
    export: bool = False,
    export_format: str = "csv",
    export_path: str = "",
    encoding: str = "utf-8",
    workers: int = 1,
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    global MAX_PROCESSES
    MAX_PROCESSES = workers

    _check_required_values(weighted, syntactic_categories)
    _check_weight_comb_option(weight_comb)

    preprocessed_corpus_context = _load_preprocessed_corpus_context(
        tagged_corpus_context,
        pos_filter=lambda t: filter(lambda a: a[1] in syntactic_categories, t),
        stop_words_filter=None if stop_words is None else lambda t: filter(lambda a: a[0] not in stop_words, t),
        lemma=lemma,
    )

    weighted_keywords, top_t_vertices = _keywords_extraction_from_preprocessed_context(
        preprocessed_corpus_context,
        window=window,
        top_p=top_p,
        top_t=top_t,
        directed=directed,
        weighted=weighted,
        conn_with_original_ctx=conn_with_original_ctx,
        solver=solver,
        max_iter=max_iter,
        tol=tol,
        weight_comb=weight_comb,
        mu=mu,
    )

    sorted_weighted_keywords = list(sort_dict_by_value(weighted_keywords).items())

    _export_result(
        sorted_weighted_keywords, export=export, export_format=export_format, export_path=export_path, encoding=encoding
    )

    return sorted_weighted_keywords, top_t_vertices


def _check_export_option(export, export_format):
    if not isinstance(export, bool):
        raise ValueError("'export' must be a boolean value.")

    if export:
        if export_format is None:
            raise ValueError("'export' should not be None.")

        if export_format.lower() not in ["csv", "json"]:
            raise ValueError("Only 'csv' or 'json' is allowed as export format.")


def _check_weight_comb_option(weight_comb):
    if not isinstance(weight_comb, str):
        raise ValueError("'weight_comb' must be a str value.")

    if weight_comb is None:
        raise ValueError("'weight_comb' should not be None.")

    if weight_comb not in (
        "avg",
        "norm_avg",
        "log_norm_avg",
        "gaussian_norm_avg",
        "sum",
        "norm_sum",
        "log_norm_sum",
        "gaussian_norm_sum",
        "max",
        "norm_max",
        "log_norm_max",
        "gaussian_norm_max",
        "len_log_norm_max",
        "len_log_norm_avg",
        "len_log_norm_sum",
        "gcvalue",
    ):
        raise ValueError(
            "Unspported weight_comb '%s'! "
            "Options are 'avg', 'norm_avg', 'log_norm_avg', 'gaussian_norm_avg', 'sum', "
            "'norm_sum', 'log_norm_sum', 'gaussian_norm_sum', 'max', 'norm_max',"
            " 'log_norm_max', 'gaussian_norm_max', "
            "'len_log_norm_max', 'len_log_norm_avg', 'len_log_norm_sum', 'gcvalue'. " % weight_comb
        )


def keywords_extraction_from_corpus_directory(
    corpus_dir: str,
    encoding: str = "utf-8",
    solver: str = "pagerank",
    max_iter: int = 100,
    tol: float = 1e-4,
    window: int = 2,
    top_p: float = 0.3,
    top_t: Optional[int] = None,
    directed: bool = False,
    weighted: bool = False,
    syntactic_categories: Set[str] = {"NNS", "NNP", "NN", "JJ"},
    stop_words: Set[str] = None,
    lemma: bool = False,
    weight_comb: str = "norm_max",
    mu: int = 5,
    export: bool = False,
    export_format: str = "csv",
    export_path: str = "",
    workers: int = 1,
) -> Tuple[List[Tuple[str, float]], Dict[str, float]]:
    _check_export_option(export, export_format)
    _check_weight_comb_option(weight_comb)

    tokenised_sentences = CorpusContent2RawSentences(corpus_dir, encoding=encoding)

    return keywords_extraction_from_segmented_corpus(
        tokenised_sentences,
        solver=solver,
        max_iter=max_iter,
        tol=tol,
        window=window,
        top_p=top_p,
        top_t=top_t,
        directed=directed,
        weighted=weighted,
        syntactic_categories=syntactic_categories,
        stop_words=stop_words,
        lemma=lemma,
        weight_comb=weight_comb,
        mu=mu,
        export=export,
        export_format=export_format,
        export_path=export_path,
        encoding=encoding,
        workers=workers,
    )
