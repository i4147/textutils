from setuptools import setup

packages = ["textcaret", "textcaret.functions"]
package_data = {"": ["*"]}
install_requires = [
    "matplotlib>=3.4.2,<4.0.0",
    "neattext>=0.1.0,<0.2.0",
    "nltk>=3.6.2,<4.0.0",
    "spacy>=3.1.1,<4.0.0",
    "sumy>=0.8.1,<0.9.0",
    "textblob>=0.15.3,<0.16.0",
    "textstat>=0.7.1,<0.8.0",
    "wordcloud>=1.8.1,<2.0.0",
]
setup_kwargs = {
    "name": "textcaret",
    "version": "0.0.1",
    "description": "Simplified NLP Toolkit for unifying common Natural Language Processing Tasks",
    "long_description": "# textcaret\nSimplified NLP Toolkit for common NLP Tasks. Unifying common Natural Language Processing task\n\n\n#### Why TextCaret\n+ The problem: performing common NLP Task such as summarization,sentiment analysis,etc are essential however you may need to use different libraries and write different codes for performing the same set of task on different texts\n+ The goal of TextCaret is to simplify this task by providing a unified framework to \nperform these common NLP Tasks\n\n\n\n\n#### Installation\ntextcaret is available on pypi hence you can install using pip\n```bash\npip install textcaret\n```\n\n#### Benefits and Features\n+ Generate Reports for Text Analysis\n+ Text Summarization\n+ Text Visualization\n\t- wordcloud\n\t- word frequency plots\n\t- word length distribution\n\t- etc\n+ Sentiment Analysis\n+ Text Generation *\n+ etc\n\n\n#### Usage\n```python\n>>> import textcaret as tc \n>>> docx = tc.TextCaret(text='your text goes here')\n>>>\n>>> docx.visual_report()\n>>> docx.summary_report()\n>>> docx.sentiment_report()\n>>> docx.general_report()\n```\n\n#### Perform Text Visualization For Insights\n+ This generates wordcloud plots,token and tags frequency plots, word length distribution and more.\n```python\n>>> from textcaret import TextViz\n>>> s = \"your text\"\n>>> viz = TextViz(s)\n>>> viz.visualize()\n>>> # Save Plot\n>>> viz.safe_figure('mynewplot.png')\n```\n\n#### Perform TextSummarization\n+ In NLP Text Summarization is the process of shortening a set of data computationally, to create a subset (a summary) that represents the most important or relevant information within the original content.[wiki]\n+ It is the process of finding the most informative sentence in a document.\n+ TextCaret uses several extractive algorithms for generating summary\n\n```python\n>>> from textcaret import TextSummarizer\n>>> s = \"your text\"\n>>> summarizer = TextSummarizer(s)\n>>> summarizer.summarize()\n```\n\n#### Perform Sentiment Analysis\n+ In NLP, Sentiment Analysis is the process of identifying the emotions/sentiment or feeling in a given text either as positive,negative or neutral.\n+ It is a form of text classification\n+ TextCaret uses the famous textblob library behind the scene to generate sentiments of given text\n\n```python\n>>> from textcaret import TextSentiment\n>>> docx = TextSentiment(\"I love coding and teaching.John hates mangoes so bad he doesn't eat it\")\n>>> \n>>> docx.sentiment()\n{'sentence': \"I love coding and teaching.John hates mangoes so bad he doesn't eat it\", 'sentiment': Sentiment(polarity=-0.09999999999999992, subjectivity=0.6333333333333333)}\n>>> \n>>> docx.sentiment()['sentiment']\nSentiment(polarity=-0.09999999999999992, subjectivity=0.6333333333333333)\n>>> \n>>> docx.sentiment()['sentiment'].polarity\n-0.09999999999999992\n>>> \n>>> docx.sentiment()['sentiment'].subjectivity\n0.6333333333333333\n>>> \n```\n\n####  Perform Sentiment on Splitted/Tokenized Sentences\n```python\n>>> docx.split_sentence=True\n>>> \n>>> docx.sentiment()\n{'sentiment': [('I love coding and teaching', 0.5), (\"John hates mangoes so bad he doesn't eat it\", -0.6999999999999998)]}\n>>> \n\n```\n\n\n#### Dependencies\nTextcaret is built ontop of powerful and common NLP libraries such as below\n+ NLTK\n+ TextBlob\n+ Sumy\n+ Neattext\n+ Matplotlib\n+ Wordcloud\n+ Spacy\n\n#### .\n+ Maintainer: Jesse E.Agbe(JCharis)\n+ Jesus Saves @JCharisTech\n\n#### Contributions\n+ Notice a bug, please let us know\n+ We appreciate contributions of anykind.\n+ Happy Coding!!! :smiley:\n\n\n\n\n\n\n\n",
    "author": "Jesse E.Agbe(JCharis)",
    "author_email": "jcharistech@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/jcharistech/textcaret",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.8,<4.0",
}
setup(**setup_kwargs)
