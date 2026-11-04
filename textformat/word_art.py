class WordArt:
    @staticmethod
    def banner(text, char="█", width=50):
        top = char * width
        middle = f"{char} {text.center(width - 4)} {char}"
        return f"{top}\n{middle}\n{top}"
