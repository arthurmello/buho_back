import os
import shutil
import json
from pathlib import Path


def clear_directory(directory):
    if os.path.exists(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
            print(f"{directory} cleared!")


def dump_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        json.dump(data, f)


def load_json(path):
    try:
        with open(path) as file:
            result = json.load(file)
    except Exception as e:
        print(f"Can't load json from {path}. Error: {e}")
        result = []
    return result
