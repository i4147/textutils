CC_OGONEK = "\u0328"
CC_GRAVE = "\u0300"
CC_ACUTE = "\u0301"
CC_TILDE = "\u0303"
CC_DOT_ABOVE = "\u0307"
I_UPPER_OGONEK = "\u012e"
I_LOWER_OGONEK = "\u012f"
I_UPPER_GRAVE = "\u00cc"
I_UPPER_ACUTE = "\u00cd"
I_UPPER_TILDE = "\u0128"


class CaseMapperTrAz:
    TABLE_TOLOWER = str.maketrans("İI", "iı")
    TABLE_TOUPPER = str.maketrans("iı", "İI")

    @staticmethod
    def lower(s):
        s = s.replace("I\u0307", "I")
        return s.translate(CaseMapperTrAz.TABLE_TOLOWER).lower()

    @staticmethod
    def upper(s):
        return s.translate(CaseMapperTrAz.TABLE_TOUPPER).upper()


class CaseMapperLi:
    MAP_TOLOWER = {
        "I" + CC_ACUTE: "i" + CC_DOT_ABOVE + CC_ACUTE,
        "J" + CC_ACUTE: "j" + CC_DOT_ABOVE + CC_ACUTE,
        I_UPPER_OGONEK + CC_ACUTE: I_LOWER_OGONEK + CC_DOT_ABOVE + CC_ACUTE,
        "I" + CC_GRAVE: "i" + CC_DOT_ABOVE + CC_GRAVE,
        "J" + CC_GRAVE: "j" + CC_DOT_ABOVE + CC_GRAVE,
        I_UPPER_OGONEK + CC_GRAVE: I_LOWER_OGONEK + CC_DOT_ABOVE + CC_GRAVE,
        "I" + CC_TILDE: "i" + CC_DOT_ABOVE + CC_TILDE,
        "J" + CC_TILDE: "j" + CC_DOT_ABOVE + CC_TILDE,
        I_UPPER_OGONEK + CC_TILDE: I_LOWER_OGONEK + CC_DOT_ABOVE + CC_TILDE,
        I_UPPER_ACUTE: "i" + CC_DOT_ABOVE + CC_ACUTE,
        I_UPPER_GRAVE: "i" + CC_DOT_ABOVE + CC_GRAVE,
        I_UPPER_TILDE: "i" + CC_DOT_ABOVE + CC_TILDE,
    }

    @staticmethod
    def lower(s):
        s = s.replace("I", "\u0069\u0307")
        for u, l in CaseMapperLi.MAP_TOLOWER.items():
            s = s.replace(u, l)
        return s.lower()

    @staticmethod
    def upper(s):
        return s.upper()
