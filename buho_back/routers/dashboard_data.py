from fastapi import APIRouter
import os
from buho_back.services.storage.file_management import (
    get_dashboard_data_directory,
    load_json,
)

router = APIRouter()


@router.get("/")
def dashboard_data(user, deal):
    dashboard_data_directory = get_dashboard_data_directory(user, deal)
    return load_json(dashboard_data_directory)
