def ripper(regex, text):
    vec, lf = [], 0
    for match in regex.finditer(text):
        rt = match.start()
        if sp := text[lf:rt]:
            vec.append(sp)
        vec.append(match.group())
        lf = match.end()
    if lf < len(text):
        vec.append(text[lf:])
    return vec
