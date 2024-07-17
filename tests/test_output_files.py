import json
import pytest
from fastapi.testclient import TestClient
from buho_back.main import app
from buho_back.models import OutputFileRequest
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
client = TestClient(app)
user = "test_user"


@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before running tests
    client.get(f"/input_files/reset?user_id={user}")
    yield
    # Cleanup after running tests
    client.get(f"/input_files/reset?user_id={user}")


def test_get_output_files():
    response_from_output_files = client.get(f"/output_files/")
    assert response_from_output_files.status_code == 200
    assert len(response_from_output_files.json()) > 0


def test_generate_output_files():
    file_for_test = "file_for_test.pdf"
    file_path = os.path.join(current_dir, file_for_test)
    files = [("files", open(file_path, "rb"))]
    response_from_upload = client.post(
        f"/input_files/upload?user_id={user}", files=files
    )

    response_from_output_files = client.get(f"/output_files/")
    output_files = response_from_output_files.json()

    for filename in output_files:
        response_from_generate_output_files = client.post(
            f"/output_files/generate?user_id={user}",
            json={"filename": filename},
            headers={"Content-Type": "application/json"},
        )
        assert response_from_generate_output_files.status_code == 200

        content_disposition = response_from_generate_output_files.headers.get(
            "Content-Disposition"
        )
        assert content_disposition is not None
        assert f'attachment; filename="{filename}"' in content_disposition
        time.sleep(30)
