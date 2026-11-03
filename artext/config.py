class Config:
    error_rate = 0.25
    pos_determiner = ['DET']
    target_determiner = ['a', 'an', 'the']
    error_rate_determiner = 0.5
    error_rate_determiner_ins_del_replace = ['1', '1', '1']
    pos_preposition = ['IN']
    target_preposition = ['with', 'at', 'from',
                          'into', 'of', 'to', 'in', 'for', 'on', 'by']
    target_preposition_full = ['with', 'at', 'from', 'into', 'during',
                               'until', 'of', 'to', 'in', 'for', 'on',
                               'by', 'about', 'before', 'without', 'after',
                               'under', 'within', 'along', 'through']
    error_rate_preposition = 0.5
    error_rate_preposition_ins_del_replace = ['1', '1', '1']
    pos_noun = ['NN', 'NNS']
    error_rate_noun_number = 0.5
    pos_verb = ['VB', 'VBP', 'VBZ', 'VBG', 'VBD', 'VBN']
    error_rate_verb_form = 0.5
    error_rate_verb_form_del_replace = ['0.5', '0.5']
    pos_adv = ['RB']
    error_rate_adv_form = 0.5
    pos_adj = ['JJ', 'JJR', 'JJS']
    error_rate_adj_form = 0.5
    target_punc = [',', '.', '?', '!', ':', ';']
    error_rate_punctuation = 0.5
    error_rate_typo = 0.09
    error_rate_swap = 0.05
    samples = 1
    separator = '\n'
    path_protected_tokens = None
