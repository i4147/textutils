from PIL import Image
from bmtext.meta import parse_file
from bmtext.pil import LoadedFont


def main():
    font = parse_file("tests/fixtures/raleway-30/raleway-thin-32.fnt")
    loaded = LoadedFont(font)
    letters = {}
    chars = {}
    for letter in "To":
        char = font.char_map[ord(letter)]
        im = loaded.char_image(char)
        letters[letter] = im
        chars[letter] = char
    t = letters["T"]
    o = letters["o"]
    ct = chars["T"]
    to = chars["o"]

    mask = Image.new("L", (300, 100), "black")
    x = 0
    mask.paste(t, (x, 11))
    x += 14 - 3
    mask.paste(o, (x + 1, 15))
    x += 14 - 3
    mask.paste(t, (x, 11))
    x += 14 - 3 + 1
    mask.paste(o, (x, 15))

    yellow = Image.new("RGB", mask.size, "yellow")
    red = Image.new("RGB", mask.size, "red")

    yellow.paste(red, (0, 0), mask=mask)
    yellow.show()


if __name__ == "__main__":
    main()
