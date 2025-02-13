"""
Script used to remove sensitive information from dataset, and compress for publication
"""

import json
import os
from typing import List

import tqdm

from . import utils
from . import path_tools
from . import metadata
from . import process_data
from .webserver import webserver
from . import mac_lookup

import shutil

from PIL import Image

def copy_files(out_base_dir: str, fn: str):
    os.makedirs(os.path.join(out_base_dir, fn), exist_ok=True)
    shutil.copytree(
        os.path.join(path_tools.REPO_BASE_DIR, fn), os.path.join(out_base_dir, fn),
        copy_function=shutil.copy,
        dirs_exist_ok=True
        )

def copy_file(out_base_dir: str, fn: str):
    os.makedirs(os.path.dirname(os.path.join(out_base_dir, fn)), exist_ok=True)
    shutil.copy(os.path.join(path_tools.REPO_BASE_DIR, fn), os.path.join(out_base_dir, fn))

def compress_photo_list(fns: List[str], out_photos_dir: str, target_height: int):
    # Compress photos
    for p in tqdm.tqdm(fns):
        # Convert filename to object location folder
        path = path_tools.get_photo_dir(p)
        input_path = os.path.join(path_tools.PHOTOS_DIR, path)
        output_path = os.path.join(out_photos_dir, path)
        
        # Skip existing outputs to save time
        #if os.path.isfile(output_path):
        #    continue

        image: Image.Image = Image.open(input_path)

        # Compress to fixed height, keep aspect
        if image.height > target_height:
            new_image = image.resize((int(image.width / image.height * target_height), target_height))
        else:
            new_image = image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save
        new_image.save(output_path)

def compress_photos(meta: metadata.Metadata, out_photos_dir: str):
    # Wide photos of chargers, reduce quality to blur any license plates / people in the background
    compress_photo_list([f for p in meta.parks.values() for f in p.get_photos()], out_photos_dir, 300)
    # Photos of charger labels, keep high-res
    compress_photo_list([f for c in meta.chargers.values() for f in c.get_photos()], out_photos_dir, 1200)



def export_data(meta: metadata.Metadata, out_chargers_dir: str):
    # Filter experiments, keep only overview.json files, and censor MAC address
    for plug in tqdm.tqdm(meta.plugs.values()):
        plug_folder = plug.get_folder()

        input_path = os.path.join(path_tools.CHARGER_DIR, plug_folder, "overview.json")
        output_path = os.path.join(out_chargers_dir, plug_folder, "overview.json")

        with open(input_path, "r") as f:
            data = json.load(f)
        
        data["hle_mac"] = utils.vertict_val({mac_lookup.redact_mac(k): v for k, v in utils.split_multiple(data["hle_mac"]).items()})
        data["phy_mac"] = utils.vertict_val({mac_lookup.redact_mac(k): v for k, v in utils.split_multiple(data["phy_mac"]).items()})

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f)


def main():
    meta = metadata.read_charger_metadata_table()

    output_dir = os.path.abspath(os.path.join(path_tools.REPO_BASE_DIR, "..", "EV-Study-Analysis-Export"))
    print("Exporting to ", output_dir)

    if(input("Are you sure? This will overwrite the folder! [y]") != "y"):
        return

    if True:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    if True:

        print("Copying static files")
        copy_files(output_dir, "proc_code")
        copy_file(output_dir, "data/metadata/parks.csv")
        copy_file(output_dir, "data/metadata/chargers.csv")
        copy_file(output_dir, "data/metadata/plugs.csv")
        copy_file(output_dir, "data/.gitignore")
        copy_file(output_dir, "data/.gitattributes")
        copy_file(output_dir, "data/run_server.bat")
        copy_file(output_dir, "data/run_server.sh")

        copy_file(output_dir, ".gitignore")
        copy_file(output_dir, ".gitattributes")
        copy_file(output_dir, "install.sh")
        copy_file(output_dir, "plots.ipynb")
        copy_file(output_dir, "requirements.txt")
        copy_file(output_dir, "README.md")

    if True:
        print("Compressing photos")
        compress_photos(meta, os.path.join(output_dir, "data", "photos"))
    if True:
        print("Copying data")
        #shutil.rmtree(os.path.join(output_dir, "data", "chargers"))
        export_data(meta, os.path.join(output_dir, "data", "chargers"))

if __name__ == "__main__":
    main()