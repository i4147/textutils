from mytextgrid.io.parser import fulltext_format


def read_from_file(path, encoding=None):
    textgrid_dict = fulltext_format.parse_textgrid_file(path, encoding)
    textgrid_obj = fulltext_format.dict_to_textgrid(textgrid_dict)
    return textgrid_obj


def read_from_stream(*args, **kwds):
    textgrid_dict = fulltext_format.parse(*args, **kwds)
    textgrid_obj = fulltext_format.dict_to_textgrid(textgrid_dict)
    return textgrid_obj
