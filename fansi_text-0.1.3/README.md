# fansi_text

A Python module for formatting text with ANSI escape codes.

## Installation

```
pip install fansi_text
```

## Usage

```python
from fansi_text import Red

print(Red("Red text"))
```

```python
from fansi_text import RGBColor

print(RGBColor("RGB Text", 200, 130, 60))
```

You can also form complex combinations of overlapping effects.
```python
import fansi_text as ft

print(
    ft.Bold("Bold, " + ft.Green("green and bold. "))
    + "Then normal text. Then "
    + ft.Underline(ft.Overline("under and over lined. "))
    + "Next "
    + ft.Italic(
        "italics. Add "
        + ft.Yellow("yellow " + ft.Bold("and bold too! ") + "Then back to yellow and italics, ")
        + "then just italics, "
    )
    + "and finally back to normal."
)
```
A demo_all method is provided to allow for testing all supported colours and effects in your terminal.
```python
import fansi_text as ft

ft.demo_all()
```

The full list of colours and effects are shown below (notes per [Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code#Select_Graphic_Rendition_parameters)).
Note that support for each code varies between terminals.


|ANSI Code              |Name                     |Example | Note                     |
|-----------------------|-------------------------|--------|-----------------------------------------------------------------|
|0                      |Reset                   |         |All attributes become turned off                                       |
|1                      |Bold                    | **Bold Text** |As with faint, the color change is a PC (SCO / CGA) invention.         |
|2                      |Faint                   | <span style="opacity:0.6">Faint Text</span> |May be implemented as a light font weight like bold.                   |
|3                      |Italic                  | *Italic Text* |Not widely supported. Sometimes treated as inverse or blink.           |
|4                      |Underline               | <u>Underlined Text</u> |Style extensions exist for Kitty, VTE, mintty, iTerm2 and Konsole.     |
|5                      |SlowBlink               | *(Example not supported in README)* |Sets blinking to less than 150 times per minute                        |
|6                      |FastBlink               | *(Example not supported in README)* |MS-DOS ANSI.SYS, 150+ per minute; not widely supported                 |
|7                      |Invert                  | <span style="color:white;background-color:black">Inverted</span> |Swap foreground and background colors; inconsistent emulation          |
|8                      |Conceal                 |            |Not widely supported.    |
|9                      |Strikethrough           | ~~Strikethrough Text~~ |Characters legible but marked as if for deletion. Not supported in Terminal.app.                                |
|10                     |Font0                   | - |Default Font             |
|11                     |Font1                   | - |Select alternative font n − 10                                         |
|12                     |Font2                   | - |Select alternative font n − 10                                         |
|13                     |Font3                   | - |Select alternative font n − 10                                         |
|14                     |Font4                   | - |Select alternative font n − 10                                         |
|15                     |Font5                   | - |Select alternative font n − 10                                         |
|16                     |Font6                   | - |Select alternative font n − 10                                         |
|17                     |Font7                   | - |Select alternative font n − 10                                         |
|18                     |Font8                   | - |Select alternative font n − 10                                         |
|19                     |Font9                   | - |Select alternative font n − 10                                         |
|20                     |FrakturFont             | *(Example not supported in README)* |Rarely supported         |
|21                     |DoubleUnderlined        | <span style="text-decoration: underline double">Double Underline</span> |Double-underline per ECMA-48 but often disables bold intensity.|
|26                     |ProportionalSpacing     | - |ITU T.61 and T.416, not known to be used on terminals                  |
|30                     |Black                   | <span style="color:black">Black Text</span> |Set text colour to black |
|31                     |Red                     | <span style="color:red">Red Text</span> |Set text colour to red   |
|32                     |Green                   | <span style="color:green">Green Text</span> |Set text colour to green |
|33                     |Yellow                  | <span style="color:gold">Yellow Text</span> |Set text colour to yellow|
|34                     |Blue                    | <span style="color:blue">Blue Text</span> |Set text colour to blue  |
|35                     |Magenta                 | <span style="color:magenta">Magenta Text</span> |Set text colour to magenta                                             |
|36                     |Cyan                    | <span style="color:cyan">Cyan Text</span> |Set text colour to cyan  |
|37                     |White                   | <span style="color:white;background-color:black">White Text</span> |Set text colour to white |
|38                     |RGBColor                | <span style="color:rgb(172,100,112)">RGBColor(172,100,112)</span> |Use with parameters e.g. RGBColor('Text', 200, 130, 60)                |
|40                     |BgBlack                 | <span style="background-color:black;color:white">Text</span> |Set black background     |
|41                     |BgRed                   | <span style="background-color:red">Text</span> |Set red background       |
|42                     |BgGreen                 | <span style="background-color:green">Text</span> |Set green background     |
|43                     |BgYellow                | <span style="background-color:yellow">Text</span> |Set yellow background    |
|44                     |BgBlue                  | <span style="background-color:blue">Text</span> |Set blue background      |
|45                     |BgMagenta               | <span style="background-color:magenta">Text</span> |Set magenta background   |
|46                     |BgCyan                  | <span style="background-color:cyan">Text</span> |Set cyan background      |
|47                     |BgWhite                 | <span style="background-color:white;color:black">Text</span> |Set white background     |
|48                     |RGBBgColor              | <span style="background-color:rgb(172,100,112)">RGBBgColor(172,100,112)</span> |Use with parameters e.g. RBGBgColor('Text', 200, 130, 60)            |
|51                     |Framed                  | <span style="border:1px solid black;padding:2px">Framed Text</span> |Implemented as "emoji variation selector" in mintty.                   |
|52                     |Encircled               | <span style="border-radius:50%;border:1px solid black;padding:2px">Encircled Text</span> |                         |
|53                     |Overlined               | <span style="text-decoration: overline">Overlined Text</span> |Not supported in Terminal.app                                          |
|58                     |UnderlineColor          | *(Example not supported in README)* |Not in standard; implemented in Kitty, VTE, mintty, and iTerm2. Next arguments are 5;n or 2;r;g;b.              |
|60–64                  |Ideogram effects        | *(Example not supported in README)* |Rarely supported         |
|73                     |Superscript             | <sup>Superscript</sup> |Implemented only in mintty                                             |
|74                     |Subscript               | <sub>Subscript</sub> |                         |
|90                     |BrightBlack             | <span style="color:gray">Bright Black Text</span> |Set text colour to bright black (gray)                                 |
|91                     |BrightRed               | <span style="color:#ff5555">Bright Red Text</span> |Set text colour to bright red                                          |
|92                     |BrightGreen             | <span style="color:#55ff55">Bright Green Text</span> |Set text colour to bright green                                        |
|93                     |BrightYellow            | <span style="color:#ffff55">Bright Yellow Text</span> |Set text colour to bright yellow                                       |
|94                     |BrightBlue              | <span style="color:#5555ff">Bright Blue Text</span> |Set text colour to bright blue                                         |
|95                     |BrightMagenta           | <span style="color:#ff55ff">Bright Magenta Text</span> |Set text colour to bright magenta                                      |
|96                     |BrightCyan              | <span style="color:#55ffff">Bright Cyan Text</span> |Set text colour to bright cyan                                         |
|97                     |BrightWhite             | <span style="color:white">Bright White Text</span> |Set text colour to bright white                                        |
100       |BgBrightBlack     | <span style="background-color:gray;color:white">Bright Black Background</span> |Set bright black (gray) background |
|101       |BgBrightRed       | <span style="background-color:#ff5555">Bright Red Background</span> |Set bright red background |
|102       |BgBrightGreen     | <span style="background-color:#55ff55">Bright Green Background</span> |Set bright green background |
|103       |BgBrightYellow    | <span style="background-color:#ffff55;color:black">Bright Yellow Background</span> |Set bright yellow background |
|104       |BgBrightBlue      | <span style="background-color:#5555ff;color:white">Bright Blue Background</span> |Set bright blue background |
|105       |BgBrightMagenta   | <span style="background-color:#ff55ff">Bright Magenta Background</span> |Set bright magenta background |
|106       |BgBrightCyan      | <span style="background-color:#55ffff;color:black">Bright Cyan Background</span> |Set bright cyan background |
|107       |BgBrightWhite     | <span style="background-color:white;color:black">Bright White Background</span> |Set bright white background |