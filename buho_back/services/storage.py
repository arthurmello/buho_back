import os
import shutil
import json
from pathlib import Path
from buho_back.config import settings
from buho_back.utils import ChromaClient

vectordb_directory = settings.VECTORDB_DIRECTORY


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


def get_vector_store(user_id):
    user_vector_store_directory = os.path.join(vectordb_directory, user_id)
    if os.path.exists(user_vector_store_directory):
        try:
            chroma_client = ChromaClient(user_vector_store_directory)
            vector_store = chroma_client.get_collection()
        except Exception as e:
            print(
                f"Couldn't load vectorstore from {user_vector_store_directory}. Error: {e}"
            )
            vector_store = None
    else:
        vector_store = None
    return vector_store
