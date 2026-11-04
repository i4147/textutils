import argparse
import hashlib
import platform
import shutil
import ssl
import stat
import subprocess
import sys
import urllib.request
import zipfile
import os

import certifi

import logging

log = logging.getLogger("ptxlogger")


def _update_version(version: str):
    global GODOT_VERSION
    global GODOT_VERSION_TAG
    global GODOT_TEMPLATE_VERSION_STRING
    global CACHE_DIR
    global GITHUB_RELEASE_BASE
    GODOT_VERSION = version
    GODOT_VERSION_TAG = "{}-stable".format(GODOT_VERSION)
    GODOT_TEMPLATE_VERSION_STRING = "{}.stable".format(GODOT_VERSION)
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".godot_versions", GODOT_VERSION)

    GITHUB_RELEASE_BASE = "https://github.com/godotengine/godot/releases/download/{}".format(GODOT_VERSION_TAG)


_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _asset_name_for_platform() -> str:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        return "Godot_v{}_macos.universal.zip".format(GODOT_VERSION_TAG)
    elif system == "Linux":
        arch = "arm64" if machine in ("aarch64", "arm64") else "x86_64"
        return "Godot_v{}_linux.{}.zip".format(GODOT_VERSION_TAG, arch)
    elif system == "Windows":
        return "Godot_v{}_win64.exe.zip".format(GODOT_VERSION_TAG)
    else:
        raise RuntimeError("Unsupported platform: {}".format(system))


def _export_templates_asset_name() -> str:
    return "Godot_v{}_export_templates.tpz".format(GODOT_VERSION_TAG)


def _template_install_dir() -> str:
    system = platform.system()
    if system == "Linux":
        return os.path.join(
            os.path.expanduser("~"), ".local/share/godot/export_templates", GODOT_TEMPLATE_VERSION_STRING
        )
    elif system == "Darwin":
        return os.path.join(
            os.path.expanduser("~"), "Library/Application Support/Godot/export_templates", GODOT_TEMPLATE_VERSION_STRING
        )
    elif system == "Windows":
        return os.path.join(os.environ["APPDATA"], "Godot/export_templates", GODOT_TEMPLATE_VERSION_STRING)
    else:
        raise RuntimeError("Unsupported platform: {}".format(system))


def _remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def _download(url: str, destination: str) -> None:
    log.info("Downloading {} ...".format(url))
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with urllib.request.urlopen(url, context=_SSL_CONTEXT) as response, open(destination, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


_SUMS_CACHE: dict[str, dict[str, str]] = {}


def _get_release_sums() -> dict[str, str]:
    if GODOT_VERSION_TAG in _SUMS_CACHE:
        return _SUMS_CACHE[GODOT_VERSION_TAG]

    sums_path = os.path.join(CACHE_DIR, "SHA512-SUMS.txt")
    _download("{}/SHA512-SUMS.txt".format(GITHUB_RELEASE_BASE), sums_path)

    sums: dict[str, str] = {}
    with open(sums_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, filename = parts
        filename = filename.lstrip("*")
        sums[filename] = digest.lower()

    os.remove(sums_path)
    _SUMS_CACHE[GODOT_VERSION_TAG] = sums
    return sums


def _verify_checksum(file_path: str, asset_name: str) -> None:
    sums = _get_release_sums()
    expected = sums.get(asset_name)
    if expected is None:
        _remove_if_exists(file_path)
        raise RuntimeError(
            "No checksum entry for '{}' in {}'s SHA512-SUMS.txt; ".format(asset_name, GODOT_VERSION_TAG)
            + "refusing to use this download."
        )

    hasher = hashlib.sha512()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    actual = hasher.hexdigest()

    if actual != expected:
        _remove_if_exists(file_path)
        raise RuntimeError(
            "Checksum mismatch for '{}': expected {}, got {}. ".format(asset_name, expected, actual)
            + "The downloaded file was deleted; it may be corrupted or tampered with."
        )

    log.info("Checksum verified for {}.".format(asset_name))


def _get_godot_version(godot_path: str) -> str | None:
    try:
        result = subprocess.run([godot_path, "--version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _cached_binary_path() -> str | None:
    system = platform.system()
    if system == "Darwin":
        candidate = os.path.join(CACHE_DIR, "Godot.app/Contents/MacOS/Godot")
    elif system == "Windows":
        candidate = os.path.join(CACHE_DIR, "Godot_v{}_win64.exe".format(GODOT_VERSION_TAG))
    else:
        machine = platform.machine().lower()
        arch = "arm64" if machine in ("aarch64", "arm64") else "x86_64"
        candidate = os.path.join(CACHE_DIR, "Godot_v{}_linux.{}".format(GODOT_VERSION_TAG, arch))
    return candidate if os.path.exists(candidate) else None


def _download_and_extract_godot() -> str:
    asset_name = _asset_name_for_platform()
    zip_path = os.path.join(CACHE_DIR, asset_name)
    _download("{}/{}".format(GITHUB_RELEASE_BASE, asset_name), zip_path)
    _verify_checksum(zip_path, asset_name)

    log.info("Extracting {} ...".format(zip_path))
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(CACHE_DIR)
    os.remove(zip_path)

    binary_path = _cached_binary_path()
    if binary_path is None:
        raise RuntimeError(
            "Extracted {} but couldn't locate the Godot executable under {}. ".format(asset_name, CACHE_DIR)
            + "The archive's internal layout may not match what this script expects -- check its contents manually."
        )

    if platform.system() != "Windows":
        os.chmod(binary_path, os.stat(binary_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    return binary_path


def resolve_godot(gd_cmd: str, version: str) -> str:
    _update_version(version)
    path_godot = shutil.which(gd_cmd)
    if path_godot is not None:
        version_string = _get_godot_version(path_godot)
        if version_string is not None and version_string.startswith(GODOT_VERSION):
            log.info("Using Godot on PATH ({}, version {}).".format(path_godot, version_string))
            return path_godot
        else:
            log.info(
                "WARNING: 'godot' on PATH is version '{}', ".format(version_string)
                + "not the pinned version '{}'. Ignoring it and using a ".format(GODOT_VERSION)
                + "separately managed copy of {} instead.".format(GODOT_VERSION)
            )

    cached = _cached_binary_path()
    if cached is not None:
        log.info("Using cached Godot {} at {}.".format(GODOT_VERSION, cached))
        return cached

    log.info("Godot {} not found on PATH or in cache; downloading...".format(GODOT_VERSION))
    return _download_and_extract_godot()


def ensure_export_templates(version: str) -> None:
    _update_version(version)
    template_dir = _template_install_dir()
    if os.path.exists(template_dir) and any(os.scandir(template_dir)):
        log.info("Export templates for {} already installed at {}.".format(GODOT_VERSION, template_dir))
        return

    asset_name = _export_templates_asset_name()
    tpz_path = os.path.join(CACHE_DIR, asset_name)
    _download("{}/{}".format(GITHUB_RELEASE_BASE, asset_name), tpz_path)
    _verify_checksum(tpz_path, asset_name)

    log.info("Installing export templates to {} ...".format(template_dir))
    os.makedirs(template_dir, exist_ok=True)
    with zipfile.ZipFile(tpz_path) as zf:
        for member in zf.namelist():
            if not member.startswith("templates/") or member == "templates/":
                continue
            relative_path = member[len("templates/") :]
            target_path = os.path.join(template_dir, relative_path)
            if member.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zf.open(member) as source, open(target_path, "wb") as out_file:
                shutil.copyfileobj(source, out_file)
    os.remove(tpz_path)
