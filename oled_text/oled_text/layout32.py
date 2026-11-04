from __init__ import BigLine, SmallLine


def layout_3small():
    return {1: SmallLine(0, 0), 2: SmallLine(0, 10), 3: SmallLine(0, 20)}


def layout_1big_1small():
    return {
        1: BigLine(0, 0, font="Arimo.ttf", size=18),
        2: SmallLine(0, 19),
    }


def layout_2medium():
    return {1: BigLine(0, 1, font="FreeSans.ttf", size=14), 2: BigLine(0, 17, font="FreeSans.ttf", size=14)}


def layout_1big():
    return {
        1: BigLine(0, 8, font="FreeSans.ttf", size=20),
    }


def layout_iconleft_1big():
    return {
        1: BigLine(0, 8, font="FontAwesomeSolid.ttf", size=24),
        2: BigLine(26, 10, font="FreeSans.ttf", size=20),
    }


def layout_iconright_1big():
    return {
        1: BigLine(100, 8, font="FontAwesomeSolid.ttf", size=24),
        2: BigLine(0, 10, font="FreeSans.ttf", size=20),
    }
