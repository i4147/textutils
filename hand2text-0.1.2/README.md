# Hand2Text

A Python package that converts handwritten PDF notes to text using OCR and AI.

[![PyPI version](https://badge.fury.io/py/hand2text.svg)](https://badge.fury.io/py/hand2text)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

Hand2Text helps you convert your handwritten PDF notes into editable text. It's designed for students, researchers, or anyone who takes handwritten notes and wants to digitize them.

The process is straightforward:
1. **PDF to Images**: Breaks down your PDF into individual page images
2. **Text Extraction**: Uses AI to read your handwriting and convert it to text
   - **Vision AI First**: OpenAI's latest models can read handwriting directly from images
   - **OCR Backup**: Falls back to traditional OCR + AI cleanup if needed

## Installation

### Quick Install

```bash
pip install hand2text
```

### Prerequisites

- Python 3.10 or higher
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (required for fallback method)
- OpenAI API key

### Setup

1. Install the package:
   ```bash
   pip install hand2text
   ```

2. Get an OpenAI API key from https://platform.openai.com/api-keys

3. Create a `.env` file in your working directory:
   ```env
   OPENAI_API_KEY=your_key_here
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Only needed on Windows for OCR fallback
   ```

## Usage

### Command Line

Processing a PDF is as simple as:

```bash
hand2text path/to/your/notes.pdf
```

This creates a text folder with your converted notes. The images are cleaned up automatically, so you just get the text files you care about.

### Python API

If you want to integrate this into your own code:

```python
from hand2text import main

# Process with default output folders
main("path/to/your/notes.pdf")

# Or specify where you want the output
main("notes.pdf", "temp_images", "my_text_output")
```

## How It Works

### PDF to Image Conversion
Uses PyMuPDF to convert each page of the PDF to a PNG image.

### Text Extraction
Hand2Text tries to be smart about extracting your handwritten text:

#### Primary Method: Vision AI
First, it sends your handwritten pages directly to OpenAI's vision models (like GPT-4o). These models have gotten surprisingly good at reading handwriting - often better than traditional OCR.

#### Fallback Method: OCR + AI Cleanup
If the vision models aren't available or fail, Hand2Text falls back to:
1. **OCR**: Uses Tesseract to scan the text (with some image preprocessing to help it out)
2. **AI Cleanup**: Sends the messy OCR output to GPT-3.5 to fix obvious mistakes and clean things up

## Example Output

```bash
$ hand2text lecture_notes.pdf
[MAIN] Starting pipeline with lecture_notes.pdf -> lecture_notes_images -> lecture_notes_text
[MAIN] Finished PDF to images. Listing images...
[MAIN] Found images: ['page_1.png', 'page_2.png', 'page_3.png']
[VISION] Trying model: gpt-4o
[VISION] Successfully used model: gpt-4o
[MAIN] Saved transcribed text to lecture_notes_text/page_1.txt
...
[COMBINE] Combined 3 text files into lecture_notes_text/lecture_notes_combined.txt
```

## What You Need

- **OpenAI API Key**: This does the heavy lifting for reading your handwriting
- **Tesseract OCR**: Optional backup if you want the OCR fallback (most people won't need this)
- **Python 3.10+**: Any recent Python version will work

## Development

### Setting up for development

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Install pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

### Code quality

This project uses modern Python tooling:
- **Ruff**: Fast linting and formatting
- **MyPy**: Type checking
- **Pre-commit**: Automatic checks before commits

Run checks manually:
```bash
poetry run ruff check hand2text/     # Linting
poetry run ruff format hand2text/    # Formatting
poetry run mypy hand2text/           # Type checking
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes (linting runs automatically on commit)
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Links

- **PyPI**: https://pypi.org/project/hand2text/
- **GitHub**: https://github.com/alihaskar/hand2text
- **Issues**: https://github.com/alihaskar/hand2text/issues
