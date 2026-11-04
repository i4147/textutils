import pytextrank
import spacy
import scattertext as st

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("textrank", last=True)


convention_df = st.SampleCorpora.ConventionData2012.get_data().assign(
    parse=lambda textrank_df: textrank_df["Combined"].apply(nlp),
)

corpus = st.CorpusFromParsedDocuments(
    convention_df,
    category_col="Response Variable",
    parsed_col="parse",
    feats_from_spacy_doc=st.PyTextRankPhrases(),
).build()
