import os
import re


def extract_number(filename: str) -> float:
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float("inf")


def combine_texts(input_dir: str, combined_name: str = "combined.txt") -> None:
    txt_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".txt")]
    txt_files.sort(key=extract_number)
    combined_path = os.path.join(input_dir, combined_name)
    with open(combined_path, "w", encoding="utf-8") as outfile:
        for fname in txt_files:
            with open(os.path.join(input_dir, fname), encoding="utf-8") as infile:
                outfile.write(infile.read())
            outfile.write("\n\n")
    print(f"[COMBINE] Combined {len(txt_files)} text files into {combined_path}")
    for fname in txt_files:
        if fname != combined_name:
            os.remove(os.path.join(input_dir, fname))
    print(f"[COMBINE] Deleted original .txt files, kept only {combined_name}")
