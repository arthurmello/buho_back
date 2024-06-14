import os
import shutil
from langchain_community.vectorstores import Chroma
import json
from pathlib import Path
from app.config import settings
from app.utils import embeddings

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


def get_vector_store():
    if os.path.exists(vectordb_directory):
        try:
            vector_store = Chroma(
                persist_directory=vectordb_directory, embedding_function=embeddings
            )
        except Exception as e:
            print(f"Couldn't load vectorstore from {vectordb_directory}. Error: {e}")
            vector_store = None
    else:
        vector_store = None
    return vector_store
