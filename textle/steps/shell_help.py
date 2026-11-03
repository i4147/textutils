import sys

if sys.platform == "win32":
    MV = "move"
    CP = "copy"
else:
    MV = "mv"
    CP = "cp"
