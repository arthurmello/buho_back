from fastapi import APIRouter, UploadFile
from typing import List
import time
import os
from buho_back.services.storage.file_management import (
    clear_directory,
    get_summaries_directory,
    get_input_files_directory,
    get_vectordb_directory,
)
from buho_back.services.storage.vectordb import get_vectordb
from buho_back.services.preprocessing import (
    calculate_embedding_cost,
    create_chunks,
    create_vectordb,
    load_file,
    create_summaries,
    extension_loaders,
)

allowed_extensions = extension_loaders.keys()
router = APIRouter()


@router.get("/")
async def get_files(user: str = "user", deal: str = "deal"):
    vectordb = get_vectordb(user, deal)
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
async def reset_files(user: str = "user", deal: str = "deal"):
    clear_directory(get_input_files_directory(user, deal))
    clear_directory(get_vectordb_directory(user, deal))
    clear_directory(get_summaries_directory(user, deal))
    return {"message": "Vector database reset successfully"}


@router.post("/upload")
async def upload_files(files: List[UploadFile], user: str = "user", deal: str = "deal"):
    start_time = time.time()

    chunks = []
    input_files_directory = get_input_files_directory(user, deal)
    await reset_files(user, deal)
    if not os.path.exists(input_files_directory):
        os.makedirs(input_files_directory)

    for file in files:
        if file.filename.endswith(tuple(allowed_extensions)):
            bytes_data = file.file.read()
            filename = os.path.join(input_files_directory, file.filename)
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

    create_vectordb(chunks, user, deal)
    create_summaries(chunks, user, deal)
    clear_directory(input_files_directory)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to preprocess files: {total_runtime} s")
    return {"message": "Files uploaded successfully", "cost": embedding_cost}
