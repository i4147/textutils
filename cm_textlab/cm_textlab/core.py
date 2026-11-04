import csv
import re
import string
from collections import Counter
from pathlib import Path

CHINESE_PUNCTUATION = "，。！？；：、（）《》“”‘’【】——……￥·"
ENGLISH_PUNCTUATION = string.punctuation
STOPWORDS = {
    "的",
    "了",
    "和",
    "是",
    "在",
    "我",
    "也",
    "有",
    "就",
    "不",
    "人",
    "都",
    "一",
    "一个",
    "the",
    "and",
    "of",
    "to",
    "in",
    "a",
    "is",
    "that",
    "for",
    "it",
    "with",
}

SAMPLES = {
    "三国片段": "话说天下大势，分久必合，合久必分。周末七国分争，并入于秦。及秦灭之后，楚汉分争，又并入于汉。",
    "红楼片段": "满纸荒唐言，一把辛酸泪。都云作者痴，谁解其中味。",
    "西游片段": "混沌未分天地乱，茫茫渺渺无人见。自从盘古破鸿蒙，开辟从兹清浊辨。",
    "水浒片段": "试看书林隐处，几多俊逸儒流。虚名薄利不关愁，裁冰及剪雪，谈笑看吴钩。",
    "英文演讲片段": "I have a dream that one day this nation will rise up and live out the true meaning of its creed.",
}


def list_samples():
    return list(SAMPLES)


def load_sample_text(name):
    if name not in SAMPLES:
        raise KeyError(f"没有名为 {name} 的样本，可用样本：{list_samples()}")
    return SAMPLES[name]


def clean_punctuation(text, punctuation=None):
    punctuation = punctuation or CHINESE_PUNCTUATION + ENGLISH_PUNCTUATION
    table = str.maketrans("", "", punctuation)
    return str(text).translate(table)


def cut_words(text, min_len=1, remove_stopwords=True):
    try:
        import jieba

        words = [word.strip() for word in jieba.lcut(str(text)) if word.strip()]
    except ModuleNotFoundError:
        words = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z]+", str(text))
    if remove_stopwords:
        words = [word for word in words if word not in STOPWORDS]
    return [word for word in words if len(word) >= min_len]


def char_frequency(text, ignore_punctuation=True):
    if ignore_punctuation:
        text = clean_punctuation(text)
    chars = [char for char in str(text) if not char.isspace()]
    return dict(Counter(chars).most_common())


def word_frequency(text, min_len=1, remove_stopwords=True):
    text = str(text)
    if re.search(r"[\u4e00-\u9fff]", text):
        words = cut_words(text, min_len=min_len, remove_stopwords=remove_stopwords)
    else:
        words = re.findall(r"[A-Za-z]+", text.lower())
        if remove_stopwords:
            words = [word for word in words if word not in STOPWORDS]
        words = [word for word in words if len(word) >= min_len]
    return dict(Counter(words).most_common())


def top_words(text, n=20, min_len=1):
    return list(word_frequency(text, min_len=min_len).items())[:n]


def save_wordfreq_csv(wordfreq, filename):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = wordfreq.items() if isinstance(wordfreq, dict) else wordfreq
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["词语", "次数"])
        writer.writerows(items)
    return str(path)


def make_wordcloud(text, filename="wordcloud.png", width=900, height=600, background_color="white"):
    from wordcloud import WordCloud

    words = word_frequency(text, min_len=2)
    wc = WordCloud(width=width, height=height, background_color=background_color, font_path=None)
    wc.generate_from_frequencies(words)
    wc.to_file(filename)
    return filename
