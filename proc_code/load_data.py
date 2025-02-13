"""
Utilities for reading the result.json and backup.bak.txt files coming from the data collector.
"""


from __future__ import annotations
from typing import Any, List, Tuple, TypeVar, Dict

from dataclasses import dataclass
import glob
import os
from typing import Dict, List, NamedTuple
import numpy as np
import csv
import json

from . import metadata
from . import types
from . import path_tools


#Find all results nested inside data
def find_experiment_folders(base: str):
    res = []

    for root, dirs, files in os.walk(base):
        if "backup.bak.txt" in files:
            res.append(root)
            
                
    return res

#Link experiment folders to chargers
def read_plug_experiments(plug: types.Plug):

    plug.experiments = []
    for exp_folder in find_experiment_folders(plug.get_path()):
        plug.experiments.append(types.Experiment(
            exp_folder,
            None, None,
            types.ExperimentResult()
        ))

#Rebuild the result.json file from backup.bak.txt
#If the data collector crashed before finishing
def regenerate_result_json(folder) -> bool:
    entries = []
    with open(os.path.join(folder, "backup.bak.txt")) as fr:
        for line in fr:
            line = line.strip()
            if len(line) > 0:
                entries.append(json.loads(line))

    trace = [{"trace": [], "data": []}]

    for entry in entries:
        if entry["type"] == "TRACE_ENTER":
            new_elem = {
                "version": entry["version"],
                "type": "TRACE",
                "trace": entry["trace"],
                "start_time": entry["time"],
                "end_time": None,
                "data": []
            }
            if new_elem["trace"][:-1] != trace[-1]["trace"]:
                print("Trace mismatch")
                return False
            
            trace[-1]["data"].append(new_elem)
            trace.append(new_elem)

        elif entry["type"] == "TRACE_LEAVE":
            if entry["trace"] != trace[-1]["trace"]:
                print("Trace mismatch")
                return False
            
            trace[-1]["end_time"] = entry["time"]
            trace = trace[:-1]

        else:
            new_elem = {
                "version": entry["version"],
                "type": "ENTRY",
                "trace": entry["trace"],
                "time": entry["time"],
                "data_type": entry["type"],
                "data": entry["data"]
            }
            if new_elem["trace"] != trace[-1]["trace"]:
                print("Trace mismatch")
                return False
            
            trace[-1]["data"].append(new_elem)

    with open(os.path.join(folder, "result.json"), "w") as fw:
        json.dump(trace[0]["data"][0], fw, indent = 2)

    return True

class DataEntry(NamedTuple):
    name: str
    trace: List[str]
    
    time: str
    data: Any
class TraceEntry(NamedTuple):
    name: str
    trace: List[str]

    content: List[TraceEntry | DataEntry]
    start_time: str
    end_time: str

    def find_data(self, type: str, after: int = -1) -> List[Tuple[int, DataEntry]]:
        return [(i, v) for i, v in enumerate(self.content) if isinstance(v, DataEntry) and v.name == type and i > after]
    def entries(self, after: int = -1) -> List[Tuple[int, DataEntry]]:
        return [(i, v) for i, v in enumerate(self.content) if isinstance(v, DataEntry) and i > after]
    def traces(self, after: int = -1) -> List[Tuple[int, TraceEntry]]:
        return [(i, v) for i, v in enumerate(self.content) if isinstance(v, TraceEntry) and i > after]

def parse_dataentry(j: Any) -> DataEntry:
    return DataEntry(
        name = j["data_type"],
        trace = j["trace"],
        time = j["time"],
        data = j["data"]
    )

def parse_trace(j: Any) -> TraceEntry:
    #print(j)
    return TraceEntry(
        name = j["trace"][-1],
        trace = j["trace"],

        content = [parse_entry(jj) for jj in j["data"]],
        start_time = j["start_time"],
        end_time = j["start_time"]
    )

def parse_entry(j: Any) -> DataEntry | TraceEntry:
    #print(j)
    if j["version"] != 1:
        raise ValueError("Unknown entry version")
    if j["type"] == "TRACE":
        return parse_trace(j)
    if j["type"] == "ENTRY":
        return parse_dataentry(j)
    raise ValueError(j["type"])

def try_read_result(folder) -> TraceEntry | None:
    result_file_path = os.path.join(folder, "result.json")
    if os.path.isfile(result_file_path):
        with open(result_file_path) as f:
            try:
                root_trace = json.load(f)
                return parse_trace(root_trace)
            except Exception as e:
                print("Corrupted " + result_file_path)
                raise 
                exit(0)
    else:
        print("Not found " + folder)

def read_result(folder) -> TraceEntry | None:
    res = try_read_result(folder)
    if res is not None:
        return res

    if not regenerate_result_json(folder):
        print("Failed to regenerate " + folder)
        return None

    return try_read_result(folder)
