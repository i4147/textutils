import os
import sys
import time
from distutils.log import error

alphs = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]


def renderText(string, writetime):
    os.system("clear")
    os.system("clear")
    for char in f"{string}\n":
        sys.stdout.write(f"{char}")
        sys.stdout.flush()
        time.sleep(writetime)


def deleteText(wait):
    time.sleep(wait)
    os.system("clear")


def PythonRunner():
    for char in "User@Desktop $ bash -f python.sh":
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.1)
    time.sleep(0)
    getboy = input("\nEnter Your Filename: ")
    exec(open(getboy).read())
