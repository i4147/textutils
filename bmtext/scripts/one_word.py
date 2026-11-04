from PIL import Image
from bmtext.meta import parse_file
from bmtext.pil import BMText


def main():
    im = Image.new("RGB", (320, 180), color=(160, 160, 255))
    bm = BMText(im)
    font = parse_file("tests/fixtures/raleway-30/raleway-thin-32.fnt")
    bm.text((5, 5), "Antidisestablishmentarianism\nThorough\nSHOUTING!!!\nTomato?", font, fill="blue")
    im.save("assets/rendered_text.png")
    im.show()


if __name__ == "__main__":
    main()
