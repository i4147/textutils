import time
from tkinter import *


def printing(text_, time_=0.1):
    for i in text_:
        time.sleep(time_)
        print(i, end="", flush=True)
