def is_empty(file: str, log: bool = False):
    try:
        with open(file, "r") as f:
            print(file, "is empty") if log and len(f.read()) == 0 else print(file, "is not empty") if log else None
            return len(f.read()) == 0
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def append(file: str, text: str, newline: bool = True, log: bool = False):
    try:
        with open(file, "a") as f:
            f.write(text) if not newline else f.write(f"\n{text}") if not is_empty(file) else f.write(text)
            print(f'Appended "{text}" to "{file}"') if log else None
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def write(file: str, text: str, log: bool = False):
    try:
        with open(file, "w", newline="\n") as f:
            f.write(text)
            print(f'Added "{text}" to "{file}"') if log else None
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def read(file: str, log: bool = False):
    try:
        with open(file, "r") as f:
            print(f.read()) if log else None
            return f.read()
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def clear(file: str, replacement: str = "", log: bool = False):
    try:
        with open(file, "w") as f:
            print(f'Cleared "{file}"') if replacement != "" or None else print(
                f"replaced {file}'s content with '{replacement}'"
            ) if log else None
            f.write(replacement)
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def does_exist(file: str, log: bool = False):
    try:
        is_empty(file)
        print(file, "does exist") if log else None
        return True
    except FileNotFoundError:
        print(file, "doesn't exist") if log else None
        return False
    except PermissionError as e:
        raise Exception("No permission to get to the file!")


def cide(file: str, text: str, log: bool = False):
    try:
        with open(file, "x") as f:
            f.write(text)
            print(f'Created "{file}" with "{text}" in it') if log else None
    except FileExistsError:
        try:
            with open(f"Error_{file}", "x") as f:
                f.write(text)
                print(f'Created "{file}" with "{text}" in it') if log else None
                raise SyntaxWarning(f"Named the file Error_{file} because the file already exists")
        except FileExistsError as e:
            raise SyntaxError("Couldn't create file")
    except Exception as e:
        raise SyntaxError(f"{e} perhaps you put in the wrong file location?")


def delete(file: str, log: bool = False):
    from os import remove as rem

    try:
        rem(file)
        print(f'Deleted "{file}"')
    except Exception as e:
        raise SyntaxError(f"{e} perhaps the file is already deleted?")
