__version__ = "0.1.0"
import time
import sys


def animate(text, delay):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)


def pause(delay):
    time.sleep(delay)
