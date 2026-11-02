* Python package for cleaning text, Handle Decoding and Encoding errors for all formats.
* Usage

  > Place bad text in a file and read it in python source and clean it using textclean.clean() function.
* test.py

  > from textclean.textclean import textclean
  >
  > text = open("badtext.txt").read()
  >
  > cleaned\_text = textclean.clean(text)
  >
  > print cleaned\_text