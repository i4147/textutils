import six
import requests
import csv


def reporthook(t):
    last_b = [0]

    def inner(b=1, bsize=1, tsize=None):
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b

    return inner


def download_from_url(url, path):
    if "drive.google.com" not in url:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        with open(path, "wb") as file:
            file.write(r.content)
        return
    print("downloading from Google Drive; may take a few minutes")
    confirm_token = None
    session = requests.Session()
    response = session.get(url, stream=True)
    for k, v in response.cookies.items():
        if k.startswith("download_warning"):
            confirm_token = v

    if confirm_token:
        url = url + "&confirm=" + confirm_token
        response = session.get(url, stream=True)

    chunk_size = 16 * 1024
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size):
            if chunk:
                f.write(chunk)


def unicode_csv_reader(unicode_csv_data, **kwargs):
    if six.PY2:
        csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), **kwargs)
        for row in csv_reader:
            yield [cell.decode("utf-8") for cell in row]
    else:
        for line in csv.reader(unicode_csv_data, **kwargs):
            yield line


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode("utf-8")
