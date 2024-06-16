from fastapi import APIRouter, UploadFile
from typing import List
import os
from buho_back.config import settings
from buho_back.services.storage import clear_directory, get_vector_store
from buho_back.utils import calculate_embedding_cost
from buho_back.services.preprocessing import (
    create_chunks,
    create_vector_store,
    load_document,
    create_summaries,
)

files_directory = settings.FILES_DIRECTORY
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY

router = APIRouter()


@router.get("/")
async def get_files():
    vector_store = get_vector_store()
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


@router.get("/reset")
async def reset_files():
    clear_directory(vectordb_directory)
    clear_directory(files_directory)
    clear_directory(summaries_directory)
    return {"message": "Vector database reset successfully"}


@router.post("/upload")
async def upload_files(files: List[UploadFile]):
    chunks = []
    clear_directory(
        files_directory
    )  # this first clear is for safety, just in case there were some remaining files
    if not os.path.exists(files_directory):
        os.makedirs(files_directory)

    for file in files:
        # Check if the file extension is allowed
        allowed_extensions = [".pdf", ".txt", ".docx"]
        if file.filename.endswith(tuple(allowed_extensions)):
            # Call the load_document function from services
            bytes_data = file.file.read()
            file_name = os.path.join(files_directory, file.filename)
            # Save the file locally
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

    create_vector_store(chunks)
    create_summaries(chunks)

    clear_directory(files_directory)  # we clear the directory twice to avoid cluttering
    return {"message": "Files uploaded successfully", "cost": embedding_cost}
