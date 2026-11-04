import re


class StrTemp:
    @staticmethod
    def strF2H(tok):

        def charF2H(q_ch):
            i_code = ord(q_ch)
            if i_code == 12288:
                i_code = 32
            elif 65281 <= i_code <= 65374:
                i_code -= 65248
            return chr(i_code)

        return "".join(map(charF2H, tok))

    @staticmethod
    def strH2F(tok):

        def charH2F(b_ch):
            i_code = ord(b_ch)
            if i_code == 32:
                i_code = 12288
            elif 32 <= i_code <= 126:
                i_code += 65248
            return chr(i_code)

        return "".join(map(charH2F, tok))

    @staticmethod
    def sn2pl(tok: str):
        return ""

    @staticmethod
    def pl2sn(tok: str):
        return ""

    @staticmethod
    def py2jv(tok: str):
        rsl = tok.title().replace("_", "")
        return rsl

    __plural_rules = {
        r"move$": r"moves",
        r"foot$": r"feet",
        r"child$": r"children",
        r"human$": r"humans",
        r"man$": r"men",
        r"tooth$": r"teeth",
        r"person$": r"people",
        r"([m|l])ouse$": r"\1ice",
        r"(x|ch|ss|sh|us|as|is|os)$": r"\1es",
        r"([^aeiouy]|qu)y$": r"\1ies",
        r"(?:([^f])fe|([lr])f)$": r"\1\2ves",
        r"(shea|lea|loa|thie)f$": r"\1ves",
        r"([ti])um$": r"\1a",
        r"(tomat|potat|ech|her|vet)o$": r"\1oes",
        r"(bu)s$": r"\1ses",
        r"(ax|test)is$": r"\1es",
        r"s$": r"s",
    }

    @staticmethod
    def pluralize(word):
        for k, v in StrTemp.__plural_rules.items():
            if re.search(k, word, re.I):
                # wL(f'[{word}] matched ({k}), to be replaced by ({v})')
                rsl = re.sub(k, v, word)
                return rsl
        return word + "s"


#
# def test():
#     # GTA5LosSantos -> GTA5 Los Santos
#     words = ['child', 'knife', 'potato', 'bus', 'axis', 'daily']
#     # sps = ['the_wallstreet_journal_2019', '2KGames18', 'GTA5LosSantos']
#     # st = {k: py2jv(k) for k in sps}
#     # wL(mvBrief(st))
#     plu_rsl = {w: pluralize(w) for w in words}
#     wL(mvBrief(plu_rsl))
