# What is Coltext?
Coltext - an alternative to colorama that can change the text color and background

## Content
- [Install and Import](#Install-and-Import)
- [Basic Concepts](#Basic-Concept)
- [Information on creator](#Information-on-creator)

## Install and Import
First, let's install this library. Go to cmd and write...
```sh
pip install Coltext
```
After that we open our python file and import the library...
```sh
from Coltext import Color, BackColor
```

## Basic Concept
In this library you can change the text color to Red, Blue, Green, Purple, Cyan, Black and White. You can also reset the text color to standard. The same thing works with the background. \
An example of how to change the text to Red and the background to Green
```sh
from Coltext import Color, BackColor
print(Color.Red + BackColor.Green + "Hello, World!" + Color.Clean + BackColor.Clean)
```
NOTE!!! \
On Windows 10 and Windows 11 consoles, instead of changing the color, some code may appear at the very beginning. This is due to the fact that the Windows console cannot read ANSI code. But despite this, programs such as Visual Studio Code, PyCharm, as well as the custom Windows console "Termicom" can read this ANSI code and replace the color

## Information on creator
filcher2011 == I've been a Python programmer for about 2 years now. He does small projects :) \
Telegram-channel: https://t.me/filchercode \
Financial support: https://www.donationalerts.com/r/filcher2011 
