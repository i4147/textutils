__version__ = "1.2.0"

from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from pathlib import Path


class OledText:
    fonts_folder = Path(__file__).parents[0] / "fonts/"

    def __init__(self, i2c, width=128, height=32, auto_show=True, on_draw=None):
        self.disp = adafruit_ssd1306.SSD1306_I2C(width, height, i2c)
        self.width = width
        self.height = height
        self.auto_show = auto_show
        self.layout = {}
        self.on_draw = on_draw

        self.disp.fill(0)
        self.disp.show()

        self.image = Image.new("1", (width, height))

        """
        self.fontSmall = ImageFont.truetype("fonts/ProggyTiny.ttf", 16) 
        offset = 10 => 3/6 Lines
        """

        if height == 32:
            import layout32

            self.layout = layout32.layout_3small()
        else:
            import layout64

            self.layout = layout64.layout_5small()

    def drawing(self):
        return ImageDraw.Draw(self.image)

    def text(self, text, line=1):

        if line in self.layout:
            self.layout[line].text = text
        else:
            raise KeyError("No line with key '{}' present in the current layout config.".format(line))

        if self.auto_show:
            self.show()

    def show(self):
        draw = self.drawing()
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        if self.on_draw is not None:
            self.on_draw(draw)

        for row in self.layout.values():
            draw.text((row.x, row.y), text=row.text, fill=255, font=row.font)

        self.disp.image(self.image)
        self.disp.show()

    def clear(self):
        self.disp.fill(0)
        self.disp.show()


class Line:
    def __init__(self, x, y, font, size):
        self.x = x
        self.y = y
        self.text = ""
        self.font = ImageFont.truetype(str(OledText.fonts_folder / font), size)


class SmallLine(Line):
    def __init__(self, x=0, y=0, font="ProggyClean.ttf", size=16):
        super().__init__(x=x, y=y, font=font, size=size)


class BigLine(Line):
    def __init__(self, x=0, y=0, font="FreeSans.ttf", size=16):
        super().__init__(x=x, y=y, font=font, size=size)
