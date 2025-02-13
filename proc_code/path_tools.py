"""
Paths used by the analysis scripts.
All relative to the location of this file.
"""

import os

REPO_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

DATA_BASE_DIR = os.path.join(REPO_BASE_DIR, "data")
CHARGER_DIR = os.path.join(DATA_BASE_DIR, "chargers")
PHOTOS_DIR = os.path.join(DATA_BASE_DIR, "photos")
METADATA_DIR = os.path.join(DATA_BASE_DIR, "metadata")

def get_plug_folder(id: str):
    return os.path.join(*id.split(".", 2)).replace(".", "_")

def get_plug_path(id: str):
    return os.path.join(CHARGER_DIR, get_plug_folder(id))

def get_photo_dir(fn: str):
    return '_'.join(fn.split('_')[:3]) + "/" + fn.rstrip() #Also used by webserver