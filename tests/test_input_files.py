import json
import pytest
from fastapi.testclient import TestClient
from buho_back.main import app
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
client = TestClient(app)
user = "temp_user"


@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before running tests
    client.get(f"/input_files/reset?user_id={user}")
    yield
    # Cleanup after running tests
    client.get(f"/input_files/reset?user_id={user}")


def test_get_allowed_extensions_for_input_files():
    response_from_allowed_extensions = client.get(f"/input_files/allowed_extensions/")
    assert response_from_allowed_extensions.status_code == 200
    assert len(response_from_allowed_extensions.json()) > 0


def test_upload_and_get_input_files():
    file_for_test = "file_for_test.pdf"
    file_path = os.path.join(current_dir, file_for_test)
    files = [("files", open(file_path, "rb"))]
    response_from_upload = client.post(
        f"/input_files/upload?user_id={user}", files=files
    )
    assert response_from_upload.status_code == 200

    response_from_get = client.get(f"/input_files/?user_id={user}")
    files_from_get = [item["name"] for item in response_from_get.json()]
    assert file_for_test in files_from_get


def test_reset_input_files():
    file_for_test = "file_for_test.pdf"
    file_path = os.path.join(current_dir, file_for_test)
    files = [("files", open(file_path, "rb"))]
    response_from_upload = client.post(
        f"/input_files/upload?user_id={user}", files=files
    )

    response_from_reset = client.get(f"/input_files/reset?user_id={user}")
    assert response_from_reset.status_code == 200

    response_from_get = client.get(f"/input_files/?user_id={user}")
    files_from_get = [item["name"] for item in response_from_get.json()]
    assert len(files_from_get) == 0
