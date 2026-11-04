import sys
from typing import List


def convert_short_syntax(args: List[str]) -> List[str]:
    if len(args) >= 2 and not any(arg.startswith("--") or arg == "generate" for arg in args):
        content = args[0]
        extensions = args[1:]
        return ["generate", "--content", content] + [arg for ext in extensions for arg in ("--extension", ext)]
    return args


def main() -> None:
    from .cli import cli

    if len(sys.argv) > 1 and sys.argv[1] != "--help" and not sys.argv[1].startswith("-"):
        sys.argv[1:] = convert_short_syntax(sys.argv[1:])

    cli()


if __name__ == "__main__":
    main()
