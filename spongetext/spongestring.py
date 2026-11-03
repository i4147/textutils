from random import randrange


class SpongeString:
    def __init__(self, string, spongeness=6):
        self.original = string
        self.spongeness = spongeness
        self.sponge_percentage = int(spongeness) * 10
        self.text = self.__spongefy()

    def __spongefy(self):
        text = ""
        for word in self.original.split():
            text += self.__process_word(word)
            text += " "
        return text[:-1]

    def __process_word(self, word):
        output = ""
        capitals = self.__capital_positions(word)
        c_index = 0
        for c in word:
            if c_index in capitals:
                output += c.upper()
            else:
                output += c.lower()
            c_index += 1
        return output

    @classmethod
    def __generate_position(cls, word, positions):
        capital_letter_pos = randrange(0, len(word))
        if capital_letter_pos not in positions:
            return capital_letter_pos
        else:
            return cls.__generate_position(word, positions)

    def __capital_positions(self, word):
        capital_amount = int(len(word) * self.sponge_percentage / 100)
        positions = []
        for i in range(0, capital_amount):
            capital_letter = self.__generate_position(word, positions)
            positions.append(capital_letter)
        return positions

    def __repr__(self):
        return self.text
