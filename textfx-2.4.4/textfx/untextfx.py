import random
import string
from time import sleep
from termcolor import colored


def untypeeffect(text, color=None, delay=0.1):
    print(colored(text, color), end="", flush=True)
    sleep(1)
    for _ in text:
        print("\b \b", end="", flush=True)
        sleep(delay)


def unscrameffect(text, color=None, delay=0.1):
    scrambled = list(text)
    for i in range(len(text) + 1):
        if i < len(text):
            scrambled[i:] = random.choices(string.ascii_letters + string.punctuation + " ", k=len(text) - i)
        print("\r" + colored("".join(scrambled), color), end="", flush=True)
        sleep(delay)
    print("\r" + " " * len(text), end="", flush=True)


def unwavetext(text, color=None, delay=0.1):
    for i in range(len(text), -1, -1):
        wave = "".join([char.upper() if idx == i else char.lower() for idx, char in enumerate(text)])
        print("\r" + colored(wave, color), end="", flush=True)
        sleep(delay)
