class TextStega:
    def encode(self, CoverFilePath, EncodeFilePath):
        self.cover = open(CoverFilePath, "r")
        self.encode = open(EncodeFilePath, "r")
        self.CoverStr = self.cover.read()
        self.EncodeStr = self.encode.read()
        self.CoverStrBin = "".join(format(ord(i), "08b") for i in self.CoverStr)
        self.EncodeStrBin = "".join(format(ord(i), "08b") for i in self.EncodeStr)
        j = 0
        self.key = ""
        try:
            for i in range(len(self.EncodeStrBin)):
                temp = 0
                if self.EncodeStrBin[i] == self.CoverStrBin[j]:
                    self.key += "0"
                else:
                    while self.EncodeStrBin[i] != self.CoverStrBin[j]:
                        j += 1
                        temp += 1
                    self.key += str(temp)
                j += 1
            self.text_file = open("key.txt", "w")
            self.text_file.write(self.key)
            self.text_file.close()
            return self.key
        except IndexError:
            print("Try again!!\nLength of Covering message is not enough. Try increasing the length.")

    def decode(self, CoverFilePath, keyFilePath):
        self.cover = open(CoverFilePath, "r")
        self.key = open(keyFilePath, "r")
        self.CoverStr = self.cover.read()
        self.keyStr = self.key.read()
        self.CoverStr = "".join(format(ord(i), "08b") for i in self.CoverStr)
        self.cover.close()
        self.key.close()
        j = 0
        self.EncodedMsgBits = ""
        for i in range(len(self.keyStr)):
            if self.keyStr[i] == "0":
                self.EncodedMsgBits += self.CoverStr[j]
            else:
                j += int(self.keyStr[i])
                self.EncodedMsgBits += self.CoverStr[j]
            j += 1
        self.ascii_string = ""
        for i in range(int(len(self.EncodedMsgBits) / 8)):
            self.bit = self.EncodedMsgBits[8 * i : 8 * (i + 1)]
            self.an_integer = int(self.bit, 2)
            self.ascii_character = chr(self.an_integer)
            self.ascii_string += self.ascii_character
        self.text_file = open("EncryptedMessage.txt", "w")
        self.text_file.write(self.ascii_string)
        self.text_file.close()
        return self.ascii_string
