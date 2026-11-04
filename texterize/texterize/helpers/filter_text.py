def filterText(text):
    for char in [" ", "\n", "\r"]:
        text = text.replace(char, "")
    return text
