from __future__ import annotations
from typing import Any, List, TypeVar, Dict

def parse_float(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return float("nan")

def parse_int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None

T = TypeVar('T')
def count_elements(input_list: List[T]) -> Dict[T, int]:
    element_count: Dict[T, int] = {}
    for element in input_list:
        if element in element_count:
            element_count[element] += 1
        else:
            if element != "":
                element_count[element] = 1
    return element_count

# Verdicets are stored as:
# 2 - Definitely yes
# 1 - Mixed results
# 0 - Definitely no
# -1 - No data

def verdict_bool(dict: Dict[bool, int]) -> int:
    if dict[True] > 0 and dict[False] == 0:
        return 2 #Yes
    if dict[True] > 0 and dict[False] > 0:
        return 1 #Mixed
    if dict[True] == 0 and dict[False] > 0:
        return 0 #No
    return -1 #Unknown
    
def verdict_int(dict: Dict[int, int]) -> int:
    if dict[1] > 0:
        return 1
    return verdict_bool({False: dict[0], True: dict[2]})
    
def vertict_val(dict: Dict[Any, int]) -> str:
    keys = [k for k, v in dict.items() if v > 0]

    if len(keys) == 1:
        return str(keys[0])
    if len(keys) > 1:
        return "Multiple " + (", ".join([f"{v}x {k}" for k, v in dict.items() if v > 0]))
    return ""

def split_multiple(text: str) -> Dict[str, int]:
    if text.startswith("Multiple "):
        parts = text[len("Multiple "):].split(", ")
        splits = [part.split(" ", maxsplit=1) for part in parts]
        return {split[1]: int(split[0][:-1]) for split in splits}
    else:
        return {text: 1} # Can not recover count
