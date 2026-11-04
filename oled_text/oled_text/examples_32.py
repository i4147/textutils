import time

from __init__ import OledText
import layout32

from board import SCL, SDA
import busio

i2c = busio.I2C(SCL, SDA)

""" Examples for a 128x32 px SSD1306 oled display. For more details see the 64px examples """

oled = OledText(i2c, 128, 32)

oled.layout = layout32.layout_3small()
oled.text("Line 1", 1)
oled.text("Line 2", 2)
oled.text("Line 3", 3)
time.sleep(2)

oled.layout = layout32.layout_1big_1small()
oled.text("BigLine 1", 1)
oled.text("A much smaller line", 2)
time.sleep(2)

oled.layout = layout32.layout_2medium()
oled.text("Medium Line 1", 1)
oled.text("Medium Line 2", 2)
time.sleep(2)

oled.layout = layout32.layout_1big()
oled.text("Big Fish!", 1)
time.sleep(2)

oled.layout = layout32.layout_iconleft_1big()
oled.text("\uf062", 1)
oled.text("Bachi 123", 2)
time.sleep(2)

oled.layout = layout32.layout_iconright_1big()
oled.text("\uf52e", 1)
oled.text("Froggy go!", 2)
time.sleep(5)

oled.clear()
