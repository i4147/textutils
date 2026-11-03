class ICD(object):
    def __init__(self):
        self.ready = False
        self.md5 = "786e8592cc4853faae352033e2522711"
        self.df = None
        self.code_dict = None
        self.text_dict = None


ICD = ICD()


class SNOMED(object):
    def __init__(self):
        self.ready = False
        self.md5 = "7beba69f1d8e71f5c0b214f3795318dc"
        self.terms = None
        self.cids = None
        self.umls_cuis = None
        self.snomed_full = None


SNOMED = SNOMED()


class MeSH(object):
    def __init__(self):
        self.ready = False
        self.md5 = "something"
        self.codes = None


MeSH = MeSH()
