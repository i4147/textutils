import random, string
from printslow import printslow


def encryptext():
    encodec(fetchdata("chars"), fetchdata("key"), input("Enter a message to encrypt: "))


def decryptext():
    encodec(fetchdata("key"), fetchdata("chars"), input("Enter a message to decrypt: "))


def generatekeychar():
    chars = list(" " + string.punctuation + string.digits + string.ascii_letters)
    random.shuffle(chars)
    key = chars.copy()
    random.shuffle(key)
    while True:
        if key == chars:
            random.shuffle(key)
        else:
            break
    setdata("chars", chars)
    setdata("key", key)

    printslow("Done.")
    printslow("OUTPUT TO FILE:" + "cannot show...")


def fetchdata(filename):
    try:
        file = open(filename + ".txt", "r")
    except FileNotFoundError:
        printslow("FILE NOT FOUND: CRITICAL ERROR... TERMINATING...", 0.05)
        return 0
    temp_data = file.readlines()
    file.close()
    counter = 0
    for char in temp_data:
        temp_data[counter] = char.strip("\n")
        counter += 1
    return temp_data


def setdata(filename, charset1):
    file = open(filename + ".txt", "w")
    random.shuffle(charset1)
    for carrier in charset1:
        file.write(carrier + "\n")
    file.close()


def encodec(charset1, charset2, text1):
    text2 = ""

    for letter in text1:
        index = charset1.index(letter)
        text2 += charset2[index]

    printslow("Done.")

    number = ""
    for carrier in range(0, 20):
        number += str(random.randint(0, 9))

    if save:
        passwordfile = open("output " + number + ".txt", "w")
        passwordfile.write(text2)
        passwordfile.flush()
        passwordfile.close()
        printslow("OUTPUT TO FILE:" + text2)
    else:
        printslow("OUTPUT:" + text2)


def run():
    printslow("Encryptext V4: MESSAGE ENCRYPT AND DECRYPTOR")
    global save
    save = False
    while True:
        i = input(
            "type command to run: encrypt(e), decrypt(d), generate key and char(g), toggle saving to external file in same directory(s) and exit(q)"
        )
        if i == "g":
            generatekeychar()
        elif i == "d":
            decryptext()
        elif i == "e":
            encryptext()
        elif i == "q":
            exit()
        elif i == "h":
            printslow("WIP")
        elif i == "s":
            if save == True:
                save = False
            else:
                save = True
            printslow("Saving set to: " + str(save))
