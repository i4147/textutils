def extract_csv_cpt_data(filepath, text_search):
    import pandas as pd

    with open(filepath) as file:
        skip = next(filter(lambda x: x[1].startswith(text_search), enumerate(file)))[0]
    try:
        df = pd.read_csv(filepath, encoding="unicode_escape", skiprows=skip)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding_errors="ignore", skiprows=skip)
    return df
