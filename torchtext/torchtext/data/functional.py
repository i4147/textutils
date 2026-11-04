import re

__all__ = [
    "generate_sp_model",
    "load_sp_model",
    "sentencepiece_numericalizer",
    "sentencepiece_tokenizer",
    "numericalize_tokens_from_iterator",
]


"""
This file contains experimental functionality.
All of these are experimental, unstable, and subject to change or deletion.
"""


def generate_sp_model(filename, vocab_size=20000, model_type="unigram", model_prefix="m_user"):
    try:
        import sentencepiece as spm
    except ModuleNotFoundError:
        raise ImportWarning("Please install sentencepiece")
    spm_training_string = "--input={} \
                           --vocab_size={} \
                           --model_prefix={} \
                           --model_type={}".format(filename, vocab_size, model_prefix, model_type)
    spm.SentencePieceTrainer.train(spm_training_string)
    return None


def load_sp_model(spm_path):
    try:
        import sentencepiece as spm
    except ModuleNotFoundError:
        raise ImportWarning("Please install sentencepiece")
    sp_model = spm.SentencePieceProcessor()
    sp_model.Load(spm_path)
    return sp_model


def sentencepiece_numericalizer(sp_model):

    def _internal_func(txt_iter):
        for line in txt_iter:
            yield sp_model.EncodeAsIds(line)

    return _internal_func


def sentencepiece_tokenizer(sp_model):

    def _internal_func(txt_iter):
        for line in txt_iter:
            yield sp_model.EncodeAsPieces(line)

    return _internal_func


def custom_replace(replace_pattern):

    _patterns = list((re.compile(p), r) for (p, r) in replace_pattern)

    def _internal_func(txt_iter):
        for line in txt_iter:
            for pattern_re, replaced_str in _patterns:
                line = pattern_re.sub(replaced_str, line)
            yield line

    return _internal_func


def simple_space_split(iterator):

    for line in iterator:
        yield line.split()


def numericalize_tokens_from_iterator(vocab, iterator, removed_tokens=None):
    for tokens in iterator:
        if removed_tokens is None:
            yield iter(vocab[token] for token in tokens)
        else:
            yield iter(map(lambda x: vocab[x], filter(lambda x: x not in removed_tokens, tokens)))
