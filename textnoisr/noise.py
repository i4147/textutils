from itertools import zip_longest
import random
import string
import textnoisr.noise_unbiasing as unbias


class CharNoiseAugmenter:
    _AVAILABLE_ACTIONS = ("insert", "swap", "substitute", "delete")

    def __init__(
        self,
        noise_level: float,
        actions: tuple[str, ...] = _AVAILABLE_ACTIONS,
        character_set: tuple[str, ...] = tuple(string.ascii_letters),
        seed: int | None = None,
    ) -> None:
        self.actions = [x for i, x in enumerate(actions) if x not in actions[:i]]
        self.character_set = character_set
        self.noise_level = noise_level
        self.random = random.Random(seed)
        unsupported_actions = [a for a in self.actions if a not in CharNoiseAugmenter._AVAILABLE_ACTIONS]
        if unsupported_actions:
            msg = (
                f"You provide unsupported actions: {unsupported_actions}. Available"
                f" actions are {CharNoiseAugmenter._AVAILABLE_ACTIONS}"
            )
            raise ValueError(msg)
        if not 0 <= self.noise_level <= 1:
            msg = f"Noise level must be between 0 and 1 (included), you provide {self.noise_level}"
            raise ValueError(msg)
        if (self.noise_level > unbias.MAX_SWAP_LEVEL) & ("swap" in self.actions):
            msg = f"You cannot have a CER greater than {unbias.MAX_SWAP_LEVEL} when using action `swap`"
            raise ValueError(msg)

    def _random_success(self, p: float) -> bool:
        return self.random.random() < p

    def _random_char(self, p: float, character_set: tuple[str, ...]) -> str:
        return self._random_success(p) * self.random.choice(character_set)

    def insert_random_chars(self, text: str, p: float) -> str:
        return "".join(char + self._random_char(p, self.character_set) for char in text)

    def _choose_another_character(self, char):
        other_char = self.random.choice(self.character_set)
        while other_char == char:
            other_char = self.random.choice(self.character_set)
        return other_char

    def substitute_random_chars(self, text: str, p: float) -> str:
        return "".join(self._choose_another_character(char) if self._random_success(p) else char for char in text)

    def delete_random_chars(self, text: str, p: float) -> str:
        return "".join(["" if self._random_success(p) else char for char in text])

    def consecutive_swap_random_chars(self, text: str, p: float) -> str:
        p = unbias.unbias_swap(p, len(text))
        result = []
        was_swapped = False
        for current_char, next_char in zip_longest(text, text[1:], fillvalue=""):
            if not was_swapped:
                if self._random_success(p):
                    result.extend([next_char, current_char])
                    was_swapped = True
                    continue
                result.append(current_char)
            was_swapped = False
        return "".join(result)

    def add_noise(self, text: str | list[str]) -> str | list[str]:
        if isinstance(text, list):
            p = unbias.unbias_split_into_words(self.noise_level, text)
        else:
            p = self.noise_level
        p_effective = unbias.unbias_several_action(p, len(self.actions))
        for action in self.actions:
            match action:
                case "insert":
                    action_function = self.insert_random_chars
                case "swap":
                    action_function = self.consecutive_swap_random_chars
                case "substitute":
                    action_function = self.substitute_random_chars
                case "delete":
                    action_function = self.delete_random_chars
                case _:
                    msg = f"Action should be one of {CharNoiseAugmenter._AVAILABLE_ACTIONS!r}"
                    raise ValueError(msg)
            if isinstance(text, list):
                text = [action_function(word, p_effective) for word in text]
            else:
                text = action_function(text, p_effective)
        return text
