import math
import statistics
from . import localisation


class TextCut:
    def __init__(
        self, language=localisation.LANG_FR, width=100, tolerance=0.5, trim=True, len_func=len, normalise=False
    ):
        if width <= 0:
            raise ValueError(f"Invalid width value: {width}")

        self.language = language
        self.width = width
        self.tolerance = tolerance
        self.trim = trim
        self.len_func = len_func
        self.normalise = normalise

        self.rules = localisation.rules(language)

    def wrap(self, text):

        if self.normalise:
            return self.__normalised_wrap(text)

        probabilities = self.rules.probabilities(text)
        lines = []

        while self.len_func(text) > self.width:
            max_i = 0
            max_p = 0
            i = 1

            while self.len_func(text[:i]) < self.width + 1:
                x = i / self.width
                p = probabilities[i] * math.exp(-(((x - 1) / self.tolerance) ** 2))

                if p >= max_p:
                    max_i = i
                    max_p = p

                i += 1

            lines += [text[:max_i]]
            text = text[max_i:]
            probabilities = probabilities[max_i:]

            if self.trim:
                lines[-1] = lines[-1].strip()

        lines += [text]
        if self.trim:
            lines[-1] = lines[-1].strip()

        return lines

    def fill(self, text):

        return "\n".join(self.wrap(text))

    def __normalised_wrap(self, text):

        self.normalise = False
        defwrap = self.wrap(text)

        if len(defwrap) == 1:
            self.normalise = True
            return defwrap

        ini_width = self.width
        ini_tolerance = self.tolerance

        min_width = int(round(0.85 * self.width))
        min_tolerance = 0.25 * self.tolerance
        max_tolerance = 1.25 * self.tolerance
        num_tolerance = 51

        best_std = statistics.stdev([len(x) for x in defwrap])
        best_out = defwrap

        for w in range(min_width, ini_width + 1):
            self.width = w

            for t in range(0, num_tolerance):
                self.tolerance = min_tolerance + (max_tolerance - min_tolerance) * t / (num_tolerance - 1)

                exp_wrap = self.wrap(text)
                exp_std = statistics.stdev([len(x) for x in exp_wrap])

                if exp_std < best_std:
                    best_std = exp_std
                    best_out = exp_wrap

        self.width = ini_width
        self.tolerance = ini_tolerance
        self.normalise = True

        return best_out
