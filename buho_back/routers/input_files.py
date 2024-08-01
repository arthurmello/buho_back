from fastapi import APIRouter, UploadFile
from typing import List
import time
import os
from buho_back.services.storage.file_management import (
    clear_directory,
    get_summaries_directory,
    get_input_files_directory,
    get_vectordb_directory,
    create_folder_for_user,
    move_file_or_folder,
    list_files_and_folders,
    list_files,
    delete_object_for_user,
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
async def get_files_and_folders(user: str = "user", deal: str = "deal"):
    return list_files_and_folders(user, deal)


@router.get("/allowed_extensions")
async def get_allowed_extensions():
    return list(allowed_extensions)


@router.get("/reset")
async def reset_files(user: str = "user", deal: str = "deal"):
    # clear_directory(get_input_files_directory(user, deal))
    clear_directory(get_vectordb_directory(user, deal))
    clear_directory(get_summaries_directory(user, deal))
    return {"message": "Vector database reset successfully"}


@router.post("/create_folder")
async def create_folder(folder_path: str, user: str = "user", deal: str = "deal"):
    message = create_folder_for_user(user, deal, folder_path)
    return {"message": message}


@router.post("/move")
async def move(
    origin: str, destination: str = "", user: str = "user", deal: str = "deal"
):
    message = move_file_or_folder(origin, destination, user, deal)
    return {"message": message}


@router.post("/delete")
async def delete_file_or_folder(user: str = "user", deal: str = "deal", obj: str = ""):
    message = delete_object_for_user(user, deal, obj)
    return message


@router.post("/upload")
async def upload_files(files: List[UploadFile], user: str = "user", deal: str = "deal"):
    input_files_directory = get_input_files_directory(user, deal)
    # await reset_files(user, deal)
    if not os.path.exists(input_files_directory):
        os.makedirs(input_files_directory)

    for file in files:
        if file.filename.endswith(tuple(allowed_extensions)):
            bytes_data = file.file.read()
            filename = os.path.join(input_files_directory, file.filename)
            with open(filename, "wb") as f:
                f.write(bytes_data)
        else:
            print(
                f'File "{file.filename}" extension is not supported. Supported extensions: {allowed_extensions}'
            )

    return {"message": "Files uploaded successfully"}


@router.post("/process")
async def process_files(user: str = "user", deal: str = "deal"):
    start_time = time.time()

    chunks = []
    input_files_directory = get_input_files_directory(user, deal)
    filenames = list_files(input_files_directory)
    await reset_files(user, deal)

    for filename in filenames:
        path = os.path.join(input_files_directory, filename)
        data = load_file(path)
        chunks.extend(create_chunks(data))
        print(f'Chunks for "{filename}" processed.')

    tokens, embedding_cost = calculate_embedding_cost(
        [chunk.page_content for chunk in chunks]
    )
    print(f"Total Tokens: {tokens}")
    print(f"Embedding Cost in USD: {embedding_cost:.6f}")
    create_vectordb(chunks, user, deal)
    create_summaries(chunks, user, deal)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to preprocess files: {total_runtime} s")
    return {"message": "Files uploaded successfully", "cost": embedding_cost}
