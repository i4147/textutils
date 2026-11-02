## keyword based text extraction toolkit (keytext)

## What is it?

**keytext** is an all-in-one versatile and efficient Python package designed for keyword-based text search, manipulation, and data cleansing. Whether you need to **extract contextual information around specific keywords**, **remove unwanted terms from texts and dataframes**, or **precisely locate the positions of keywords within a Pandas DataFrame**, keytext is your indispensable toolkit for advanced robust toolkit text analysis and data management.


## Main Features
Here are just a few of the things that keytext does well:

  - Keyword Positioning: Locate the exact start and end positions of a keyword within a given text, facilitating precise information retrieval.
  - Contextual Extraction: Extract left and right texts, characters, words, and sentences surrounding a specified keyword as well as words between .
  - Flexible Configuration: Customize the number of left and right characters, words, or sentences to tailor the extraction to your specific requirements.
  - Text Between Keywords: Extract the text between two occurrences of the same keyword, offering deeper insights into the context of your data.
  - Word Removal: Efficiently remove a list of specified words from texts, enhancing text cleanliness and relevance.
  - Dataframe Cleansing: Seamlessly remove unwanted words from text columns in Pandas DataFrames, ensuring data integrity.
  - Cell Positioning in DataFrame: Identify the row and column positions of a keyword within a Pandas DataFrame, enabling precise data manipulation.
  - Random Pattern Search: Check for arbitrary patterns or regular expressions within the text data of a DataFrame, uncovering hidden insights and potential correlations.
  - Easy Integration: Integrate keytext into your Python projects effortlessly, enhancing your text processing and data cleansing workflows.


## Installation Procedure
```sh
PyPI
pip install keytext==0.3
```

## Dependencies:
- [Regex - Adds support to itterating and finding keywords from the text and dataframe](https://docs.python.org/3/library/re.html)
- [Pandas - Adds support to deal with dataframe](https://docs.python.org/3/library/index.html)


## Functionalities (with parameters description):

#### keytext.keypos_text(keyword, text)
	- Return all starting and ending position of the keyword from a giuven text
	- Output will be in list of tuples

#### keytext.extract_sents(keyword, text, format) 
	- This function extract all the sentences from a giuven text that contain the keyword
	- By default format is l, that means list of sentences. If we pass p then the outpt format will be paragraph.
    
#### keytext.extract_words(keyword, text, left, right)
	- This function extract the neighbourhood words of the keyword from a given text.
	- In case of left_w = 0, right_w = n it will provide n number of words from the right side of the keyword, n should be an integer
	- In case of left_w = m, right_w = 0 it will provide m number of words from the left side of the keyword, m should be an integer
	- In case of left_w = m, right_w = n it will provide m number of words from the left side of the keyword, n number of words from the right side of the keyword
    
#### keytext.extract_chr(keyword, text, left_chr, right_chr)
    - This function extract the neighbourhood charecters of the keyword from a given text.
	- In case of left_chr = 0, right_chr = n it will provide n number of charecters from the right side of the keyword, n should be an integer
	- In case of left_chr = m, right_chr = 0 it will provide m number of charecters from the left side of the keyword, m should be an integer
	- In case of left_chr = m, right_chr = n it will provide m number of charecters from the left side of the keyword, n number of charecters from the right side of the keyword

#### keytext.left_texts(keyword, text, occurrence)
	- This function will return the left side of the keyword i.e. from the keyword to beginning of the text based on all occurence of keyword
	- If we pass the 1 or 2 in occurence then it will return the left side text of 1st or 2nd occurence of the keyword from a text, Occurene should be 1,2,...,n,'all'
	- Provid ethe output in list format if occurence is "all"
	
#### keytext.right_texts(keyword, text, occurrence)
	- occurence means the repeation of the keyword in  text
	- This function will return the right side of the keyword i.e. from the keyword to ending of the text based on all occurence of keyword
	- If we pass the 1 in occurence then it will return the right side text of 1st occurence of the keyword from a text, Occurene should be 1,2,...,n,'all'
	- Provid ethe output in list format if occurence is "all"
	
#### keytext.between_fixed_keyword(keyword, text)
	- Provide the part of the text between two same keyword
	- Output will come in list format

#### keytext.between_distinct_keywords(keyword_start, keyword_end, text, keyword_start_occurence, keyword_end_occurence)
	- keyword_start_occurence indicates the the repeatition of the starting keyword in given string
	- keyword_end_occurence indicates the the repeatition of the starting  keyword in given string
	- Provide the part of the text between two distinct keyword
	- Output will come in list format
	- For getting all snap texts in list format pass keyword_start_occurence = 0 and keyword_end_occurence = 0

#### keytext.text_keyword_remover(remover_list, text, replaced_by)
	- This function remove the keyword from the text
	- Non alphanumeric charecters need to be write in regex format

### keytext.keypos_df(keyword, dataframe)
	- Return all cells position of the keyword from a giuven dataframe
	- Output will be in list of tuples

### keytext.dataframe_keyword_remover(remover_list, dataframe, replaced_by)
	- This function remove the keyword from the dataframe
	- Non alphanumeric charecters need to be write in regex format

### keytext.dataframe_pattern_finder(pattern, dataframe)
	- This function find the regex patterns from the dataframe the keyword from the dataframe
	- It will return the matched word with cell identity

## Contributing to pandas
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.
Feel free to ask questions on the [mailing list](https://groups.google.com/g/keytext)


## Change Log

0.1 (03/01/2024)
------------------
- First Release

0.2 (03/01/2024)
------------------
- Second Release

0.3 (03/01/2024)
------------------
- First Release
