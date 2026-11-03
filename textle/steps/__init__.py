from .pandoc import PandocStep
from .sinks import HTMLSink, PDFSink, TXTSink
from .tex import TeXStep
from .. import pipeline

pipeline.steps.extend([HTMLSink, PDFSink, TXTSink, TeXStep, PandocStep])
aliases = {
    "xetex": ("tex", "xelatex"),
    "pdftex": ("tex", "pdflatex"),
    "biber": ("biblatex", "biber"),
}
