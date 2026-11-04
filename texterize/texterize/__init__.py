from .helpers.filter_text import filterText
from .helpers.build_chroma import buildChroma
from .helpers.build_block import buildBlock
from .helpers.write_file import write

OUTPUT_DIRECTORY = "./texterized_image"
SUPPORTED_FILE_TYPES = ["HTML", "Word"]


def create(text, img_path, write_path=OUTPUT_DIRECTORY, output_file_type="HTML", overwrite=True):
    assert isinstance(text, str), f"Expected input of type string, found {type(text)}."
    assert output_file_type in SUPPORTED_FILE_TYPES, f"Output file type {output_file_type} not supported."

    text = filterText(text)
    chroma, chroma_shape = buildChroma(img_path, len(text))
    text_arr = buildBlock(text, chroma_shape)
    return write(text_arr, chroma, output_file_type, write_path, overwrite)


def createFromFile(text_path, img_path, write_path=OUTPUT_DIRECTORY, output_file_type="HTML", overwrite=True):
    try:
        f = open(text_path, "r")
        text = f.read()
        f.close()
    except:
        raise Exception(f"Could not open file {text_path}, aborting.")
    return create(text, img_path, write_path, output_file_type, overwrite)
