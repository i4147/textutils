import fire


def hello() -> str:
    return "kedatatext"


def main() -> None:
    fire.Fire(hello)


if __name__ == "__main__":
    main()
