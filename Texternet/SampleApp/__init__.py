# -*- coding: utf-8 -*-


import os
from Texternet import Texternet

cwd = os.getcwd()


"""
        This is the file that Texternet looks for in your 
        app directory in order to run your app. You can 
        include more methods if you need, but this
         is the basic setup of an app.
"""


def main(x, path):

    os.chdir(path)
    global cwd
    cwd = os.getcwd()
    TN = Texternet("TWILIO_SID", "TWILIO_TOKEN", "TWILIO_PHONE#")

    if not x.from_ in os.listdir("./Users"):
        Welcoming(x.from_)

    sampletext = "This is where your processing would happen"

    TN.sendMessage(x.from_, sampletext)

    print(x.from_ + " " + x.body)


def Welcoming(Name):

    cwd = os.getcwd()
    os.chdir("Users/")
    os.makedirs(Name)

    os.chdir(cwd)


"""
    You can include more methods if you need, but this is the basic setup of an app.
"""
