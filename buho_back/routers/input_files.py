from fastapi import APIRouter, UploadFile
from typing import List
import time
import os
from buho_back.config import (
    summaries_directory,
    input_files_directory,
    vectordb_directory,
)
from buho_back.services.storage.file_management import clear_directory
from buho_back.services.storage.vectordb import get_vectordb
from buho_back.services.preprocessing import (
    calculate_embedding_cost,
    create_chunks,
    create_vectordb,
    load_file,
    create_summaries,
    extension_loaders,
)

# data_directory = settings.DATA_DIRECTORY
# input_files_directory = settings.INPUT_FILES_DIRECTORY
# vectordb_directory = settings.VECTORDB_DIRECTORY

# summaries_directory = SUMMARIES_DIRECTORY
allowed_extensions = extension_loaders.keys()
router = APIRouter()


@router.get("/")
async def get_files(deal: str = "deal", user: str = "user"):
    vectordb = get_vectordb(deal, user)
    if vectordb:
        files_list = [
            name.split("/user/")[-1]
            for name in set([meta["source"] for meta in vectordb.get()["metadatas"]])
        ]
        files = [{"name": file} for file in files_list]
    else:
        files = []
    return files


@router.get("/allowed_extensions")
async def get_allowed_extensions():
    return list(allowed_extensions)


@router.get("/reset")
async def reset_files(deal: str = "deal", user: str = "user"):
    clear_directory(input_files_directory(deal, user))
    clear_directory(vectordb_directory(deal, user))
    clear_directory(summaries_directory(deal, user))
    return {"message": "Vector database reset successfully"}


@router.post("/upload")
async def upload_files(files: List[UploadFile], deal: str = "deal", user: str = "user"):
    start_time = time.time()

    chunks = []
    # user_input_files_directory = os.path.join(input_files_directory, user)
    user_input_files_directory = input_files_directory(deal, user)
    await reset_files(deal, user)
    if not os.path.exists(user_input_files_directory):
        os.makedirs(user_input_files_directory)

    for file in files:
        if file.filename.endswith(tuple(allowed_extensions)):
            bytes_data = file.file.read()
            filename = os.path.join(user_input_files_directory, file.filename)
            with open(filename, "wb") as f:
                f.write(bytes_data)
            data = load_file(filename)
            chunks.extend(create_chunks(data))
            print(f"{filename=}")
            print(f'Chunks for "{file.filename}" created.')
        else:
            print(
                f'File "{file.filename}" extension is not supported. Supported extensions: {allowed_extensions}'
            )
    tokens, embedding_cost = calculate_embedding_cost(
        [chunk.page_content for chunk in chunks]
    )

    print(f"Total Tokens: {tokens}")
    print(f"Embedding Cost in USD: {embedding_cost:.6f}")

    create_vectordb(chunks, deal, user)
    create_summaries(chunks, deal, user)
    # clear_directory(user_input_files_directory)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to preprocess files: {total_runtime} s")
    return {"message": "Files uploaded successfully", "cost": embedding_cost}
