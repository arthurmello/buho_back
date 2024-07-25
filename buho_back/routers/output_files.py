from fastapi import APIRouter
from fastapi.responses import FileResponse
from typing import Optional
from buho_back.config import settings
from buho_back.models import OutputFileRequest
from buho_back.services.file_generation.file_generation import generate_file
import time
import os
import json

data_directory = settings.DATA_DIRECTORY
input_files_directory = settings.INPUT_FILES_DIRECTORY
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY
instructions_directory = settings.INSTRUCTIONS_DIRECTORY
router = APIRouter()


@router.get("/")
async def get_output_file_names():
    files = [
        f
        for f in os.listdir(instructions_directory)
        if os.path.isfile(os.path.join(instructions_directory, f))
    ]
    file_names = set([f.split(".")[0] for f in files])
    return file_names


@router.get("/user_parameters")
async def get_output_file_user_parameters(filename):
    file_path = os.path.join(instructions_directory, f"{filename}.json")
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
    else:
        data = {}
    return data.get("user_parameters", [])


@router.post("/generate")
async def generate_output_file(
    body: OutputFileRequest, user_id: str = "user", user_parameters: dict | None = None
):
    print(user_parameters)
    start_time = time.time()
    filename = body.filename
    output_file_path = generate_file(filename, user_id, user_parameters)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to generate {filename}: {total_runtime} s")

    extension = output_file_path.split(".")[-1]
    if extension == "docx":
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    elif extension == "pptx":
        media_type = (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    elif extension == "xlsx":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = None
    return FileResponse(
        output_file_path,
        media_type=media_type,
        filename=f"{filename}",
    )
