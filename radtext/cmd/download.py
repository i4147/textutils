import docopt
from radtext.models.download import download


def main():
    argv = docopt.docopt(__doc__)
    if argv["--all"]:
        download()
    else:
        annotators = argv["--annotators"].split(",")
        download(annotators)


if __name__ == "__main__":
    main()
