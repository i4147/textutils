import random
import string
import textwrap
from PIL import Image, ImageDraw, ImageFont


def writetext(text, font_directory, font_size, image_directory, width, height, output_directory):
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    wraptext = text
    para = textwrap.wrap(wraptext, width=15)
    MAX_W, MAX_H = width, height
    img = Image.open(image_directory)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_directory, font_size)
    current_h, pad = 50, 10
    for line in para:
        w, h = draw.textsize(line, font=font)
        draw.text(((MAX_W - w) / 2, current_h), line, font=font)
        current_h += h + pad
    directory = output_directory + "\\"
    filename = f"output{id_generator()}.jpg"
    img.save(directory + filename)
    image = directory + filename
    print(f"image saved to {image}")
