from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
import random
import neattext.functions as nfx
from wordcloud import WordCloud
from textblob import TextBlob


def plot_wordcloud(docx):
    mywordcloud = WordCloud().generate(docx)
    plt.imshow(mywordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot()


def plot_mendelhall_curve(docx):
    word_length = [len(token) for token in docx.split()]
    word_length_count = Counter(word_length)
    sorted_word_length_count = sorted(dict(word_length_count).items())
    x, y = zip(*sorted_word_length_count)
    fig = plt.figure(figsize=(20, 10))
    plt.plot(x, y)
    plt.title("Plot of Word Length Distribution")
    plt.show()


def get_most_common_tokens(docx, num=10):
    clean_docx = nfx.remove_stopwords(docx)
    word_freq = Counter(clean_docx.split())
    most_common_tokens = word_freq.most_common(num)
    x, y = zip(*most_common_tokens)
    return x, y


def get_stopwords_freq(docx, num=10):
    stopwords_list = nfx.extract_stopwords(docx)
    word_freq = Counter(stopwords_list)
    most_common_tokens = word_freq.most_common(num)
    x, y = zip(*most_common_tokens)
    return x, y


def get_mendelhall_curve(docx):
    word_length = [len(token) for token in docx.split()]
    word_length_count = Counter(word_length)
    sorted_word_length_count = sorted(dict(word_length_count).items())
    x, y = zip(*sorted_word_length_count)
    return x, y


def __get_wordcloud(docx):
    mywordcloud = WordCloud().generate(docx)
    return mywordcloud


def get_most_common_pos_tags(docx, num=10):
    blob = TextBlob(docx)
    word, tag = zip(*blob.tags)
    tag_freq = Counter(tag).most_common(num)
    x, y = zip(*tag_freq)
    return x, y


def text_readability(text):
    import textstat

    docx = text
    results = {
        "flesch_reading": textstat.flesch_reading_ease(docx),
        "smog_index": textstat.smog_index(docx),
        "flesch_kincaid": textstat.flesch_kincaid_grade(docx),
        "coleman_liau": textstat.coleman_liau_index(docx),
        "ari": textstat.automated_readability_index(docx),
        "dale_chall": textstat.dale_chall_readability_score(docx),
        "difficult_words": textstat.difficult_words(docx),
        "linsear_write_formula": textstat.linsear_write_formula(docx),
        "gunning_fog": textstat.gunning_fog(docx),
        "fernandez_huerta": textstat.fernandez_huerta(docx),
        "szigriszt_pazos": textstat.szigriszt_pazos(docx),
        "gutierrez_polini": textstat.gutierrez_polini(docx),
        "crawford": textstat.crawford(docx),
    }
    return results


def plot_text_readability(text):
    x, y = zip(*text_readability())
    fig = plt.figure(figsize=(20, 10))
    plt.plot(x, y)
    plt.title("Plot of Text Readability")
    plt.show()


def visualize_text(docx, token_num=10, figsize=(20, 10), rotation=40):
    xt, yt = get_most_common_tokens(docx, num=token_num)
    xs, ys = get_stopwords_freq(docx, num=token_num)
    xm, ym = get_mendelhall_curve(docx)
    xp, yp = get_most_common_pos_tags(docx)
    mywordcloud = __get_wordcloud(docx)
    xr, yr = zip(*text_readability(docx).items())
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=figsize)
    fig.suptitle("TextViz Subplots[Vertical]")
    ax1.bar(xt, yt)
    ax1.set_title("Tokens Frequency")
    ax1.tick_params(labelrotation=rotation)
    ax2.bar(xs, ys, color="orange")
    ax2.set_title("Stopwords Frequency")
    ax2.tick_params(labelrotation=rotation)
    ax3.plot(xm, ym)
    ax3.set_title("Mendalhall Curve")
    ax4.imshow(mywordcloud, interpolation="bilinear")
    ax4.set_title("Wordcloud")
    ax5.bar(xp, yp, color="green")
    ax5.set_title("PoS Tags Frequency")
    ax5.tick_params(labelrotation=rotation)
    ax6.bar(xr, yr)
    ax6.set_title("Text Readability")
    ax6.tick_params(labelrotation=rotation)


def save_visualized_text(docx, filename, token_num=10, figsize=(20, 10), rotation=40):
    xt, yt = get_most_common_tokens(docx, num=token_num)
    xs, ys = get_stopwords_freq(docx, num=token_num)
    xm, ym = get_mendelhall_curve(docx)
    xp, yp = get_most_common_pos_tags(docx)
    mywordcloud = __get_wordcloud(docx)
    xr, yr = zip(*text_readability(docx).items())
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=figsize)
    fig.suptitle("TextViz Subplots[Vertical]")
    ax1.bar(xt, yt)
    ax1.set_title("Tokens Frequency")
    ax1.tick_params(labelrotation=rotation)
    ax2.bar(xs, ys, color="orange")
    ax2.set_title("Stopwords Frequency")
    ax2.tick_params(labelrotation=rotation)
    ax3.plot(xm, ym)
    ax3.set_title("Mendalhall Curve")
    ax4.imshow(mywordcloud, interpolation="bilinear")
    ax4.set_title("Wordcloud")
    ax5.bar(xp, yp, color="green")
    ax5.set_title("PoS Tags Frequency")
    ax5.tick_params(labelrotation=rotation)
    ax6.bar(xr, yr)
    ax6.set_title("Text Readability")
    ax6.tick_params(labelrotation=rotation)
    fig.savefig(filename)


def summarize_text(docx, num_sentence=2):
    parser = PlaintextParser.from_string(docx, Tokenizer("english"))
    summarizer_lex = LexRankSummarizer()
    summarizer_luhn = LuhnSummarizer()
    summarizer_lsa = LsaSummarizer()
    summary_for_lex = summarizer_lex(parser.document, num_sentence)
    summary_for_luhn = summarizer_luhn(parser.document, num_sentence)
    summary_for_lsa = summarizer_lsa(parser.document, num_sentence)
    summary_results = {
        "lexrank": summary_for_lex,
        "luhn": summary_for_luhn,
        "lsa": summary_for_lsa,
    }
    return summary_results


def analyze_text(docx):
    pass


def markov_chain(text):
    words = text.split(" ")
    m_dict = defaultdict(list)
    for current_word, next_word in zip(words[0:-1], words[1:]):
        m_dict[current_word].append(next_word)
    m_dict = dict(m_dict)
    return m_dict


def __generate_text(chain, count=15):
    word1 = random.choice(list(chain.keys()))
    sentence = word1.capitalize()
    for i in range(count - 1):
        word2 = random.choice(chain[word1])
        word1 = word2
        sentence += " " + word2
    sentence += "."
    return sentence


def generate_text(text, num_of_words=15):
    result_dict = markov_chain(text)
    final_result_sentence = __generate_text(result_dict, num_of_words)
    return final_result_sentence
