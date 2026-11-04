import re

ones = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "0": "",
}

teens = {
    "10": "ten",
    "11": "eleven",
    "12": "twelve",
    "13": "thirteen",
    "14": "fourteen",
    "15": "fifteen",
    "16": "sixteen",
    "17": "seventeen",
    "18": "eighteen",
    "19": "nineteen",
}

tens = {
    "1": "Del **tens**",
    "2": "twenty",
    "3": "thirty",
    "4": "forty",
    "5": "fifty",
    "6": "sixty",
    "7": "seventy",
    "8": "eighty",
    "9": "ninety",
    "0": "",
}

international = {
    "3": "thousand",
    "6": "million",
    "9": "billion",
    "12": "trillion",
    "15": "quadrillion",
    "18": "quintillion",
    "21": "sextillion",
    "24": "septillion",
    "27": "octillion",
    "30": "nonillion",
    "33": "decillion",
    "36": "undecillion",
    "39": "duodecillion",
    "42": "tredecillion",
    "45": "quattuordecillion",
    "48": "quindecillion",
    "51": "sexdecillion",
    "54": "septemdecillion",
    "57": "octodecillion",
    "60": "novemdecillion",
    "63": "vigintillion",
    "66": "unvigintillion",
    "69": "duovigintillion",
    "72": "trevigintillion",
    "75": "quattuorvigintillion",
    "78": "quinvigintillion",
    "81": "sexvigintillion",
    "84": "septvigintillion",
    "87": "octovigintillion",
    "90": "nonvigintillion",
    "93": "trigintillion",
    "96": "untrigintillion",
    "99": "duotrigintillion",
}


def get_formatted_list(raw_number):
    raw_number_length = len(raw_number)
    raw_number_length_mod_3 = raw_number_length % 3
    formatted_number = f"{raw_number}"
    n = 3

    if raw_number_length_mod_3 != 0:
        formatted_number = raw_number.rjust(raw_number_length + (3 - raw_number_length_mod_3), "0")

    formatted_list = [formatted_number[i : i + n] for i in range(0, len(formatted_number), n)]

    formatted_list.reverse()

    map_digits = []

    for index, value in enumerate(formatted_list):
        map_digits.append([index * 3, value])

    return map_digits


def get_base_text(number_string):
    l1, l2, l3 = list(number_string)
    last_two_digits = f"{l2}{l3}"
    if l1 == "0":
        if l2 == "1":
            text = teens[last_two_digits]
        else:
            text = f"{tens[l2]} {ones[l3]}"
    else:
        if l2 == "1":
            text = f"{ones[l1]} hundred and {teens[last_two_digits]}"
        elif last_two_digits == "00":
            text = f"{ones[l1]} hundred"
        else:
            text = f"{ones[l1]} hundred and {tens[l2]} {ones[l3]}"

    return text


def get_text(number_string, exponent):
    text = ""
    if number_string != "000":
        base_text = get_base_text(number_string)
        text = f"{base_text} {international[str(exponent)]}"
    return text


def convert_number_to_text(input_number):
    formatted_data = get_formatted_list(input_number)
    number_to_text = []

    for key, value in formatted_data:
        if key == 0:
            text = get_base_text(value)
        else:
            text = get_text(value, key)

        number_to_text.append(text)

    number_to_text.reverse()
    number_to_text_string = " ".join(number_to_text)
    return re.sub("[ ]+", " ", number_to_text_string)


def convert(number):
    try:
        int(number)
        return convert_number_to_text(str(number))
    except:
        raise Exception(f"Invalid Input  [ {number} ]")
