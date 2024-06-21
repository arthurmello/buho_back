from fastapi import APIRouter, UploadFile
from typing import List
import time
import os
from buho_back.config import settings
from buho_back.services.storage import clear_directory, get_vector_store
from buho_back.utils import calculate_embedding_cost
from buho_back.services.preprocessing import (
    create_chunks,
    create_vector_store,
    load_document,
    create_summaries,
    extension_loaders,
)

data_directory = settings.DATA_DIRECTORY
files_directory = settings.FILES_DIRECTORY
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY
allowed_extensions = extension_loaders.keys()
router = APIRouter()


@router.get("/")
async def get_files(user_id: str = "user"):
    vector_store = get_vector_store(user_id)
    if vector_store:
        files_list = [
            name.split("/")[-1]
            for name in set(
                [meta["source"] for meta in vector_store.get()["metadatas"]]
            )
        ]
        files = [{"name": file} for file in files_list]
    else:
        files = []
    return files


@router.get("/allowed_extensions")
async def get_allowed_extensions():
    return list(allowed_extensions)


@router.get("/reset")
async def reset_files(user_id: str = "user"):
    clear_directory(os.path.join(files_directory, user_id))
    clear_directory(os.path.join(vectordb_directory, user_id))
    clear_directory(os.path.join(summaries_directory, user_id))
    return {"message": "Vector database reset successfully"}


@router.post("/upload")
async def upload_files(files: List[UploadFile], user_id: str = "user"):
    start_time = time.time()

    chunks = []
    user_files_directory = os.path.join(files_directory, user_id)
    reset_files(user_id)
    if not os.path.exists(user_files_directory):
        os.makedirs(user_files_directory)

    for file in files:
        if file.filename.endswith(tuple(allowed_extensions)):
            bytes_data = file.file.read()
            file_name = os.path.join(user_files_directory, file.filename)
            with open(file_name, "wb") as f:
                f.write(bytes_data)
            data = load_document(file_name)
            chunks.extend(create_chunks(data))
            print(f"{file_name=}")
            print(f'Chunks for "{file.filename}" created.')
        else:
            print(
                f'File "{file.filename}" extension is not supported. Supported extensions: {allowed_extensions}'
            )

    tokens, embedding_cost = calculate_embedding_cost(chunks)

    print(f"Total Tokens: {tokens}")
    print(f"Embedding Cost in USD: {embedding_cost:.6f}")

    create_vector_store(chunks, user_id)
    create_summaries(chunks, user_id)
    clear_directory(user_files_directory)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to preprocess files: {total_runtime} s")
    return {"message": "Files uploaded successfully", "cost": embedding_cost}
