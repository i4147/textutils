import re
from datetime import datetime


def format_rupee(amount, include_symbol=True):
    sign = ""
    if amount < 0:
        sign = "-"
        amount = abs(amount)
    s = f"{amount:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"
    n = len(integer_part)
    if n <= 3:
        formatted_integer = integer_part
    else:
        last_three = integer_part[n - 3 :]
        rest = integer_part[: n - 3]
        formatted_rest_parts = []
        while len(rest) > 0:
            if len(rest) >= 2:
                formatted_rest_parts.append(rest[-2:])
                rest = rest[:-2]
            else:
                formatted_rest_parts.append(rest)
                rest = ""
        formatted_integer = ",".join(reversed(formatted_rest_parts)) + "," + last_three
    result = f"{formatted_integer}.{decimal_part}"
    if include_symbol:
        return f"{sign}₹ {result}"
    return f"{sign}{result}"


def standardize_indian_phone(phone_number_str, add_country_code=True):
    cleaned_number = re.sub(r"\D", "", str(phone_number_str))
    if len(cleaned_number) == 11 and cleaned_number.startswith("0"):
        cleaned_number = cleaned_number[1:]
    if len(cleaned_number) != 10:
        return None
    if add_country_code:
        return f"+91{cleaned_number}"
    return cleaned_number


def parse_indian_date(date_string, input_format="%d-%m-%Y"):
    try:
        return datetime.strptime(date_string, input_format)
    except ValueError:
        return None


def clean_text_basic(text_string):
    cleaned_text = re.sub(r"\s+", " ", text_string).strip()
    return cleaned_text


def remove_emoji(text_string):
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text_string)


def about():
    package_version_str = "0.3.4"
    author_name = "Amit Dutta"
    github_link = "https://github.com/notamitgamer/"
    print("\n--------------------------------------------------")
    print(f"📦 textbuddy Package Information 📦")
    print("--------------------------------------------------")
    print(f"Version: {package_version_str}")
    print("Description: Simple string and text utilities for Indian contexts.")
    print(f"\n✨ Developed with ❤️ by {author_name} ✨")
    print("I hope this package proves useful in your Python journey!")
    print(f"For more details, source code, and to report issues, visit:")
    print(f"➡️ {github_link}")
    print("--------------------------------------------------\n")
