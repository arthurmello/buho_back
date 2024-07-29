import os
import shutil
import json
from pathlib import Path
from buho_back.config import DATA_DIRECTORY


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


def get_vectordb_directory(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "vectordb")


def get_summaries_directory(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "summaries")


def get_input_files_directory(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "input_files")


def get_output_files_directory(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "output_files")


def get_chat_history_file(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "chat_history.json")


def get_qa_tracker_directory(deal, user):
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "qa_tracker")
