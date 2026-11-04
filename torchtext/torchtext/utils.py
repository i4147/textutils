import six
import requests
import csv
from tqdm import tqdm
import os
import tarfile
import logging
import re
import sys
import zipfile


def reporthook(t):
    last_b = [0]

    def inner(b=1, bsize=1, tsize=None):
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b

    return inner


def download_from_url(url, path=None, root=".data", overwrite=False):

    def _process_response(r, root, filename):
        chunk_size = 16 * 1024
        total_size = int(r.headers.get("Content-length", 0))
        if filename is None:
            d = r.headers["content-disposition"]
            filename = re.findall('filename="(.+)"', d)
            if filename is None:
                raise RuntimeError("Filename could not be autodetected")
            filename = filename[0]
        path = os.path.join(root, filename)
        if os.path.exists(path):
            logging.info("File %s already exists." % path)
            if not overwrite:
                return path
            logging.info("Overwriting file %s." % path)
        logging.info("Downloading file {} to {}.".format(filename, path))
        with open(path, "wb") as file:
            with tqdm(total=total_size, unit="B", unit_scale=1, desc=path.split("/")[-1]) as t:
                for chunk in r.iter_content(chunk_size):
                    if chunk:
                        file.write(chunk)
                        t.update(len(chunk))
        logging.info("File {} downloaded.".format(path))
        return path

    if path is None:
        _, filename = os.path.split(url)
    else:
        root, filename = os.path.split(path)

    if not os.path.exists(root):
        raise RuntimeError("Download directory {} does not exist. Did you create it?".format(root))

    if "drive.google.com" not in url:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        return _process_response(response, root, filename)
    else:
        filename = None

    logging.info("Downloading from Google Drive; may take a few minutes")
    confirm_token = None
    session = requests.Session()
    response = session.get(url, stream=True)
    for k, v in response.cookies.items():
        if k.startswith("download_warning"):
            confirm_token = v

    if confirm_token:
        url = url + "&confirm=" + confirm_token
        response = session.get(url, stream=True)

    return _process_response(response, root, filename)


def unicode_csv_reader(unicode_csv_data, **kwargs):

    maxInt = sys.maxsize
    while True:
        try:
            csv.field_size_limit(maxInt)
            break
        except OverflowError:
            maxInt = int(maxInt / 10)
    csv.field_size_limit(maxInt)

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


def extract_archive(from_path, to_path=None, overwrite=False):

    if to_path is None:
        to_path = os.path.dirname(from_path)

    if from_path.endswith((".tar.gz", ".tgz")):
        logging.info("Opening tar file {}.".format(from_path))
        with tarfile.open(from_path, "r") as tar:
            files = []
            for file_ in tar:
                file_path = os.path.join(to_path, file_.name)
                if file_.isfile():
                    files.append(file_path)
                    if os.path.exists(file_path):
                        logging.info("{} already extracted.".format(file_path))
                        if not overwrite:
                            continue
                tar.extract(file_, to_path)
            return files

    elif from_path.endswith(".zip"):
        assert zipfile.is_zipfile(from_path), from_path
        logging.info("Opening zip file {}.".format(from_path))
        with zipfile.ZipFile(from_path, "r") as zfile:
            files = []
            for file_ in zfile.namelist():
                file_path = os.path.join(to_path, file_)
                files.append(file_path)
                if os.path.exists(file_path):
                    logging.info("{} already extracted.".format(file_path))
                    if not overwrite:
                        continue
                zfile.extract(file_, to_path)
        files = [f for f in files if os.path.isfile(f)]
        return files

    else:
        raise NotImplementedError("We currently only support tar.gz, .tgz and zip achives.")
