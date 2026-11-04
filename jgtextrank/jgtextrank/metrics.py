# -*- coding: utf-8 -*-

import logging
import math
from typing import Tuple, Dict

import numpy as np

from jgtextrank.utility import MultiprocPool

_logger = logging.getLogger("jgtextrank.metrics")

__author__ = "Jie Gao <j.gao@sheffield.ac.uk>"

__all__ = [
    "_get_max_score",
    "_get_average_score",
    "_get_sum_score",
    "_term_size_normalize",
    "_log_normalise",
    "_probability_density",
    "_gaussian_normalise",
    "_get_plus_score",
    "TermGraphValue",
    "GCValue",
]


def _get_max_score(all_syntactic_units, all_vertices):
    # print("all_vertices: ", all_vertices)
    # print("collapsed_term: ", collapsed_term)
    # max_score = max([all_vertices[term_unit] / float(all_syntactic_units.count(term_unit)) for term_unit in collapsed_term.split(' ')])
    max_score = max([
        all_vertices[term_unit] / float(all_syntactic_units.count(term_unit)) for term_unit in all_syntactic_units
    ])
    return max_score


def _get_average_score(all_syntactic_units, all_vertices, unit_size):
    avg_score = _get_sum_score(all_syntactic_units, all_vertices) / float(unit_size)
    return avg_score


def _get_sum_score(all_syntactic_units, all_vertices):
    return sum([
        all_vertices[term_unit] / float(all_syntactic_units.count(term_unit)) for term_unit in all_syntactic_units
    ])


def _term_size_normalize(base_score, unit_size):
    return base_score / float(unit_size)


def _log_normalise(base_score, mu, unit_size):
    if unit_size > 1:
        # print("_log_normalise with mu=", mu, " , unit_size:", unit_size)
        base_score = base_score / math.log(unit_size, mu)
    return base_score


def _probability_density(x_value, mu, sigma):
    pd = (1 / (sigma * np.sqrt(2 * math.pi))) * math.exp(-math.pow((x_value - mu), 2) / (2 * math.pow(sigma, 2)))
    return pd


def _gaussian_normalise(base_score, mu, sigma, unit_size):
    norm_value = 1 - _probability_density(unit_size, mu, sigma)
    return base_score * float(norm_value)


def _get_plus_score(
    all_syntactic_units, boosted_term_size_range, boosted_word_length_range, combined_weight, unit_size
):
    all_syntactic_units_lengths = [len(term_unit) for term_unit in all_syntactic_units]
    min_word_length = min(all_syntactic_units_lengths)
    max_word_length = max(all_syntactic_units_lengths)
    avg_word_length = sum(all_syntactic_units_lengths) / unit_size
    plus_weight = combined_weight
    if (
        boosted_word_length_range is not None
        and boosted_term_size_range is not None
        and unit_size in boosted_term_size_range
        and min_word_length in boosted_word_length_range
        and max_word_length in boosted_word_length_range
    ):
        plus_weight = combined_weight * math.log(avg_word_length, 2)
    elif (
        boosted_word_length_range is None
        and boosted_term_size_range is not None
        and unit_size in boosted_term_size_range
    ):
        plus_weight = combined_weight * math.log(avg_word_length, 2)
    elif (
        boosted_word_length_range is not None
        and boosted_term_size_range is None
        and min_word_length in boosted_word_length_range
        and max_word_length in boosted_word_length_range
    ):
        plus_weight = combined_weight * math.log(avg_word_length, 2)

    return plus_weight


class TermGraphValue(object):
    def __init__(self, weight_comb="norm_max", mu=5, parallel_workers=1):
        self._logger = logging.getLogger("jgtextrank.metrics")
        self._logger.info(self.__class__.__name__)
        self.parallel_workers = parallel_workers
        self.weight_comb = weight_comb
        self.mu = mu

    @staticmethod
    def g_value(collapsed_term, all_vertices, weight_comb="norm_sum", mu=5, **kwargs):
        final_score = float(0)
        log2a = 0
        avg_score = 0
        sum_score = 0
        max_score = 0
        sigma = 0
        if "sigma" in kwargs:
            sigma = kwargs["sigma"]

        # all_syntactic_units = collapsed_term.split(' ')
        all_syntactic_units = collapsed_term
        unit_size = len(all_syntactic_units)
        if "len_log" in weight_comb:
            log2a = math.log2(unit_size + 0.1)
        if "avg" in weight_comb:
            avg_score = _get_average_score(all_syntactic_units, all_vertices, unit_size)
        if "sum" in weight_comb:
            sum_score = _get_sum_score(all_syntactic_units, all_vertices)
        if "max" in weight_comb:
            max_score = _get_max_score(all_syntactic_units, all_vertices)
        if weight_comb == "avg":
            final_score = avg_score
        elif weight_comb == "norm_avg":
            final_score = _term_size_normalize(avg_score, unit_size)
        elif weight_comb == "log_norm_avg":
            final_score = _log_normalise(avg_score, mu, unit_size)
        elif weight_comb == "gaussian_norm_avg":
            final_score = _gaussian_normalise(avg_score, mu, sigma, unit_size)
        elif weight_comb == "len_log_norm_avg":
            final_score = log2a * avg_score
        elif weight_comb == "sum":
            final_score = sum_score
        elif weight_comb == "norm_sum":
            final_score = _term_size_normalize(sum_score, unit_size)
        elif weight_comb == "log_norm_sum":
            final_score = _log_normalise(sum_score, mu, unit_size)
        elif weight_comb == "gaussian_norm_sum":
            final_score = _gaussian_normalise(sum_score, mu, sigma, unit_size)
        elif weight_comb == "len_log_norm_sum":
            final_score = log2a * sum_score
        elif weight_comb == "max":
            final_score = max_score
        elif weight_comb == "norm_max":
            final_score = _term_size_normalize(max_score, unit_size)
        elif weight_comb == "log_norm_max":
            final_score = _log_normalise(max_score, mu, unit_size)
        elif weight_comb == "gaussian_norm_max":
            final_score = _gaussian_normalise(max_score, mu, sigma, unit_size)
        elif weight_comb == "len_log_norm_max":
            final_score = log2a * max_score
        else:
            raise ValueError("Unsupported weight combination option: '%s'", weight_comb)

        return round(final_score, 5)

    def _is_top_t_vertices_connection(self, collapsed_term, top_t_vertices):
        return any(top_t_vertex[0] in collapsed_term for top_t_vertex in top_t_vertices)

    def _concatenate_terms(self, weighted_candidates) -> Dict[str, float]:
        return dict((" ".join(tokenised_term), score) for tokenised_term, score in weighted_candidates)

    def _get_sigma_from_all_candidates(self, collapsed_terms):
        all_terms_size = [len(collapsed_term) for collapsed_term in collapsed_terms]
        return np.std(all_terms_size)

    def weighing(self, all_candidates, all_vertices, top_t_vertices) -> Dict[str, float]:
        if all_candidates is None or len(all_candidates) == 0:
            self._logger.info("No candidate found. Skip weighing.")
            return {}

        self._logger.info(" Total [%s] candidates to weigh...", len(all_candidates))

        sigma = 0
        if "norm" in self.weight_comb:
            sigma = self._get_sigma_from_all_candidates(all_candidates)

        with MultiprocPool(processes=int(self.parallel_workers)) as pool:
            optional_params = dict()
            optional_params["weight_comb"] = self.weight_comb
            optional_params["mu"] = self.mu
            if sigma != 0:
                optional_params["sigma"] = sigma

            weighted_all_candidates = pool.starmap(
                TermGraphValue.calculate,
                [
                    (candidate, all_candidates, all_vertices, optional_params)
                    for candidate in all_candidates
                    if self._is_top_t_vertices_connection(candidate, top_t_vertices)
                ],
            )

        return self._concatenate_terms(weighted_all_candidates)

    @staticmethod
    def calculate(candidate_term, all_candidates, all_vertices, optional_params=None) -> Tuple[str, float]:
        if optional_params is None:
            optional_params = dict()

        weight_comb = "norm_max"
        if "weight_comb" in optional_params:
            weight_comb = optional_params["weight_comb"]

        mu = 5
        if "mu" in optional_params:
            mu = optional_params["mu"]

        sigma = 0
        if "sigma" in optional_params:
            sigma = optional_params["sigma"]

        final_score = TermGraphValue.g_value(candidate_term, all_vertices, weight_comb, mu, sigma=sigma)

        return (candidate_term, final_score)


class GCValue(TermGraphValue):
    def __init__(self, weight_comb="len_log_norm_avg", mu=5, parallel_workers=1):
        super().__init__(weight_comb, mu, parallel_workers)

    @staticmethod
    def _get_longer_terms(term, all_candidates):
        try:
            return [
                longer_term
                for longer_term in all_candidates
                if term != longer_term and set(term).issubset(set(longer_term))
            ]
        except AttributeError:
            import traceback

            _logger.error(traceback.format_exc())
            _logger.error("AttributeError when processing candidate term [%s]", term)
        return []

    def weighing(self, all_candidates, all_vertices, top_t_vertices) -> Dict[str, float]:
        if all_candidates is None or len(all_candidates) == 0:
            self._logger.info("No candidate found. Skip weighing.")
            return {}

        self._logger.info(" Total [%s] candidates to weigh...", len(all_candidates))
        with MultiprocPool(processes=int(self.parallel_workers)) as pool:
            weighted_all_candidates = pool.starmap(
                GCValue.calculate,
                [
                    (candidate, all_candidates, all_vertices)
                    for candidate in all_candidates
                    if self._is_top_t_vertices_connection(candidate, top_t_vertices)
                ],
            )

        self._logger.info(" all candidates gc-value computation is completed.")
        return super()._concatenate_terms(weighted_all_candidates)

    @staticmethod
    def _sum_ga_candidates(candidate_list, all_vertices):
        return sum([
            TermGraphValue.g_value(candidate, all_vertices, weight_comb="len_log_norm_avg")
            for candidate in candidate_list
        ])

    @staticmethod
    def calculate(candidate_term, all_candidates, all_vertices, optional_params=None) -> Tuple[str, float]:
        if optional_params is None:
            optional_params = dict()

        longer_terms = GCValue._get_longer_terms(candidate_term, all_candidates)
        a = len(candidate_term)
        log2a = math.log(a + 0.1, 2)
        g_a = TermGraphValue.g_value(candidate_term, all_vertices, weight_comb="len_log_norm_avg")

        if longer_terms:
            p_ta = len(longer_terms)
            sum_gb = GCValue._sum_ga_candidates(longer_terms, all_vertices)
            term_gcvalue = log2a * (g_a - (1 / p_ta) * sum_gb)
        else:
            term_gcvalue = log2a * g_a

        return (candidate_term, round(term_gcvalue, 5))
