"""
Utilities to read and write the metadata tables
"""

from __future__ import annotations
from typing import Any, List, Tuple, TypeVar, Dict

from dataclasses import dataclass
import glob
import os
from typing import Dict, List, NamedTuple
import numpy as np
import csv

from . import types
from . import path_tools

class Metadata(NamedTuple):
    parks: Dict[str, types.Park]
    chargers: Dict[str, types.Charger]
    plugs: Dict[str, types.Plug]


#Read CSV as a Dict of Dict, by first column then first row as keys.
def read_csv_to_dict(file_path: str, **reader_args):
    result: Dict[str, Dict[str, Any]] = {}
    
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile, **reader_args)
        
        if csv_reader.fieldnames is None:
            raise RuntimeError()

        for row in csv_reader:
            key = row[csv_reader.fieldnames[0]]  # The first column as the key
            result[key] = row
    
    return result

def write_csv_to_dict(file_path: str, data: List[Dict[str, Any]], **writer_args):
    cols = data[0].keys()

    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=cols, **writer_args)
        
        csv_writer.writeheader()
        csv_writer.writerows(data)

# Read tables containing experiment metadata
def read_charger_metadata_table() -> Metadata:
    parks_data_dict = read_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "parks.csv"))
    chargers_data_dict = read_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "chargers.csv"))
    plugs_data_dict = read_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "plugs.csv"))

    parks_dict = {k: types.Park.create(v) for k, v in parks_data_dict.items()}
    chargers_dict = {k: types.Charger.create(v, parks_dict) for k, v in chargers_data_dict.items()}
    plugs_dict = {k: types.Plug.create(v, chargers_dict) for k, v in plugs_data_dict.items()}

    return Metadata(parks_dict, chargers_dict, plugs_dict)

def save_charger_metadata_table(meta: Metadata):
    parks_data_dict = [{
        "ID": park.id,
        "Country": park.country, "Town": park.town,
        "Type": park.type, "Type2": park.type2,
        "Lat": str(park.lat), "Long": str(park.long),
        "Photos": park.photos, "Notes": park.notes
    } for park in meta.parks.values()]

    chargers_data_dict = [{
        "ID": charger.id,
        "Position": charger.position,
        "Manufacturer": charger.manufacturer, "Operator": charger.network, "Model": charger.model,
        "MFGYear": str(charger.mfg_year) if charger.mfg_year is not None else "", "MFGDetail": charger.mfg_detail,
        "SN": charger.sn,
        "Photos": charger.photos, "Notes": charger.notes
    } for charger in meta.chargers.values()]

    plugs_data_dict = [{
        "ID": plug.id,
        "Position": plug.position,
        "Notes": plug.notes
    } for plug in meta.plugs.values()]

    write_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "parks.csv"), parks_data_dict)
    write_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "chargers.csv"), chargers_data_dict)
    write_csv_to_dict(os.path.join(path_tools.METADATA_DIR, "plugs.csv"), plugs_data_dict)
