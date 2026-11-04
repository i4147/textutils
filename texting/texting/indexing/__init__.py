def index_nontab(tx):
    t, i = str(tx), 0
    while str.startswith(t, "\t", i) or str.startswith(t, " ", i):
        i += 1
    return i


def after_nontab(tx):
    return tx[index_nontab(tx)]
