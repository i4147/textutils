import re
import pandas as pd


def extract_words(keyword, text, left, right):
    text = text.upper()
    keyword = keyword.upper()
    text_pieces = text.split(keyword)
    if len(text_pieces) == 1:
        return None
    split_words = [piece.split() for piece in text_pieces]
    occurences = []
    for index in range(len(split_words) - 1):
        left_words = split_words[index][len(split_words[index]) - left :]
        right_words = split_words[index + 1][0:right]
        surrounded_text = " ".join(left_words + [keyword] + right_words)
        occurences.append(surrounded_text)
    return occurences


def prRed(skk):
    print("\033[31m{}\033[00m".format(skk))


def left_texts(keyword, text, occurence):
    left_part = []
    positions = keypos_text(keyword, text)
    for i in range(len(positions)):
        left_part.append(text[: positions[i][0]])
    if occurence == all:
        return left_part
    elif (occurence <= 0) or (occurence > len(positions)):
        return prRed("\t\t  Error: invalid occurence")
    else:
        return left_part[occurence - 1]


def right_texts(keyword, text, occurence):
    right_part = []
    positions = keypos_text(keyword, text)
    for i in range(len(positions)):
        right_part.append(text[positions[i][1] :])
    if occurence == all:
        return right_part
    elif (occurence <= 0) or (occurence > len(positions)):
        return prRed("\t\t  Error: invalid occurence")
    else:
        return right_part[occurence - 1]


def extract_sents(keyword, text, format):
    keyword = str(keyword).lower()
    text = text.lower()
    sentences = text.split(".")
    keyword_sentences = [sentence.strip() for sentence in sentences if keyword in sentence]
    if format.lower() == "l":
        return keyword_sentences
    elif format.lower == "p":
        return ".".join(keyword_sentences)
    else:
        pass
    return None


def between_fixed_keyword(keyword, text):
    text = text.upper()
    keyword = keyword.upper()
    positions = keypos_text(keyword, text)
    texts = []
    for i in range(len(positions)):
        if i < len(positions) - 1:
            req_text = text[positions[i][1] : positions[i + 1][0]]
            texts.append(req_text)
        else:
            req_text = text[positions[i][1] :]
            texts.append(req_text)
    return texts


def between_distinct_keywords(keyword_start, keyword_end, text, keyword_start_occurence, keyword_end_occurence):
    keyword_start = str(keyword_start).lower()
    keyword_end = str(keyword_end).lower()
    text = text.lower()
    positions_ks = keypos_text(keyword_start, text)
    positions_ke = keypos_text(keyword_end, text)
    matches = []
    for i in range(len(positions_ks)):
        for j in range(len(positions_ke)):
            if positions_ks[i] < positions_ke[j]:
                match = text[positions_ks[i - 1][1] : positions_ke[j - 1][0]]
                matches.append((positions_ks[i - 1][1], positions_ks[j - 1][0], match))
    if (
        (keyword_start_occurence > 0)
        and (keyword_end_occurence > 0)
        and (keyword_start_occurence <= len(positions_ks))
        and (keyword_end_occurence <= len(positions_ke))
    ):
        req = text[positions_ks[keyword_start_occurence - 1][1] : positions_ke[keyword_end_occurence - 1][0]]
        return req.strip()
    else:
        return (
            keyword_start
            + " keyword repeats "
            + str(len(positions_ks))
            + " times and "
            + keyword_end
            + " keyword repeats "
            + str(len(positions_ke))
            + " times. Change your occurence accordingly"
        )


def extract_chr(keyword, text, left_chr, right_chr):
    keyword = keyword.upper()
    text = text.upper()
    key = re.finditer(keyword, text)
    pos_start_end = [(match.start(), match.end()) for match in key]
    need = []
    for pos in pos_start_end:
        user_need = text[pos[0] - left_chr : pos[1] + right_chr]
        need.append(user_need)
    return need


def keypos_text(keyword, text):
    keyword = keyword.upper()
    text = text.upper()
    key = re.finditer(keyword, text)
    pos_start_end = [(match.start(), match.end()) for match in key]
    return pos_start_end


def text_keyword_remover(remover_list, text, replaced_by):
    pattern = re.compile("|".join(map(re.escape, remover_list)))
    output = pattern.sub(replaced_by, text)
    return output


def keypos_df(keyword, dataframe):
    positions = []
    keyword = str(keyword).lower()
    for i in range(dataframe.shape[0]):
        for j in range(dataframe.shape[1]):
            if type(dataframe.iat[i, j]) == str and keyword in dataframe.iat[i, j].lower():
                positions.append((i, j))
    return positions


def dataframe_keyword_remover(remover_list, dataframe, replaced_by):
    pattern = "|".join([r"{}".format(w) for w in remover_list])
    output_df = dataframe.replace(pattern, replaced_by, regex=True)
    return output_df


def dataframe_pattern_finder(pattern, dataframe):
    all_pattern = []
    for i in range(dataframe.shape[0]):
        for j in range(dataframe.shape[1]):
            if type(dataframe.iat[i, j]) == str:
                search = re.findall(pattern, dataframe.iat[i, j])
                if len(search) > 0:
                    all_pattern.append((i, j, search))
    return all_pattern
