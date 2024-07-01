from fastapi import APIRouter
from fastapi.responses import FileResponse
from buho_back.config import settings
from buho_back.models import OutputFileRequest
from buho_back.services.file_generation import generate_file
import time

data_directory = settings.DATA_DIRECTORY
input_files_directory = settings.INPUT_FILES_DIRECTORY
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY
router = APIRouter()


@router.post("/generate")
async def generate_output_file(body: OutputFileRequest, user_id: str = "user"):
    start_time = time.time()
    filename = body.filename
    output_file_path = generate_file(filename, user_id)

    end_time = time.time()
    total_runtime = round(end_time - start_time, 2)
    print(f"Time to generate {filename}: {total_runtime} s")
    return FileResponse(
        output_file_path, media_type="application/pdf", filename=f"{filename}.pdf"
    )
