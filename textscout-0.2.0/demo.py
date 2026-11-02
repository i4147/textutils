from textscout import TextAnalysis

my_text = """
Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence. It is concerned with the interactions between computers and human language.

In particular, how to program computers to process and analyze large amounts of natural language data.
"""
analysis = TextAnalysis(my_text)
report = analysis.analyze()
print(report)
print(f"Word Count: {analysis.get_word_count()}")
print(f"Estimated Reading Time (minutes): {analysis.get_estimated_reading_time()}")
