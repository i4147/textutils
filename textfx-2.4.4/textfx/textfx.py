import random
import string
from time import sleep
from termcolor import colored


def typeeffect(text, color=None, delay=0.1):
    for tp in text:
        sleep(delay)
        print(colored(tp, color), end="", flush=True)


def scrameffect(text, color=None, delay=0.1):
    scrambled = list("".join(random.choices(string.ascii_letters + string.punctuation, k=len(text))))
    for i in range(len(text) + 1):
        scrambled[:i] = text[:i]
        print("\r" + colored("".join(scrambled), color), end="", flush=True)
        sleep(delay)


def wavetext(text, color=None, delay=0.1):
    for i in range(len(text)):
        wave = "".join([char.upper() if idx == i else char.lower() for idx, char in enumerate(text)])
        print("\r" + colored(wave, color), end="", flush=True)
        sleep(delay)
