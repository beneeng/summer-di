
import itertools
import os
from typing import Any, Dict, Union
import yaml
import json

from summer.util.file_util import open_with_backup


def _get_all_entries(d, prefix):
    dot_praefix = ""
    if prefix:
        dot_praefix = f"{prefix}."
        base = [(prefix, d)]
    else:
        base = []
    if isinstance(d, dict):
        return itertools.chain(base, *[_get_all_entries(v, f"{dot_praefix}{k}") for k, v in d.items()])
    elif isinstance(d, list):
        return itertools.chain(base, *[_get_all_entries(e, f"{prefix}[{i}]") for i, e in enumerate(d)])
    return base


def explode_dict(complex_dict: Dict[str, Any]) -> Dict[str, Any]:
    entries = _get_all_entries(complex_dict, "")
    result = {k: v for k, v in entries}
    return result


def load_dict_from_file(filename: str) -> Dict:
    
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)

    _, ext = os.path.splitext(filename)
    if ext.lower() == ".yaml":
        with open(filename, "r") as ymlfile:
            return yaml.safe_load(ymlfile)
    else:
        with open(filename, "r") as f:
            return json.load(f)


def write_dict_to_file(data:Dict, filename: str):
    _, ext = os.path.splitext(filename)
    
    with open_with_backup(filename, "w+") as f:
        if ext.lower() == "yaml":
            yaml.safe_dump(data, f)
        else:
            json.dump(data, f, sort_keys=True, indent=4)

def get_by_path(d: Dict[str, Any], path: Union[str,list]) -> Any:
    if isinstance(path, str):
        return get_by_path(d, path.split('.'))

    current_elem = path[0]
    rest = path[1:]
    try:
        if not rest:
            return d[current_elem]
        else: 
            return get_by_path(d[current_elem], rest)
    except KeyError:
        raise KeyError('.'.join(path)) from None

def set_by_path(d: Dict[str, Any], path: Union[str,list], value: Any):
    if isinstance(path, str):
        return set_by_path(d, path.split('.'), value)

    current_elem = path[0]
    rest = path[1:]
 
    if not rest:
        d[current_elem] = value
    else:
        if current_elem not in d:
            d[current_elem] = {}
        next_depth = d[current_elem]
        if not isinstance(next_depth, dict):
            next_depth = {}
            d[current_elem] = next_depth
        return set_by_path(next_depth, rest, value)
