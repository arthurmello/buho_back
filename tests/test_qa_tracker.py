import json
import pytest
from fastapi.testclient import TestClient
from buho_back.main import app

client = TestClient(app)
user = "test_user"
body = {"owner": "test owner", "question": "test question"}


@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before running tests
    client.get(f"/qa_tracker/reset?user={user}")
    yield
    # Cleanup after running tests
    client.get(f"/qa_tracker/reset?user={user}")


def test_add_and_get_qa_tracker():
    response_from_add = client.post(
        f"/qa_tracker/add?user={user}", content=json.dumps(body)
    )
    assert response_from_add.status_code == 200

    response_from_get = client.get(f"/qa_tracker/?user={user}")
    assert body in response_from_get.json()["qa_tracker"]


def test_reset_and_get_qa_tracker():
    response_from_add = client.post(
        f"/qa_tracker/add?user={user}", content=json.dumps(body)
    )
    assert response_from_add.status_code == 200

    response_from_reset = client.get(f"/qa_tracker/reset?user={user}")
    assert response_from_reset.status_code == 200

    response_from_get = client.get(f"/qa_tracker/?user={user}")
    assert len(response_from_get.json()["qa_tracker"]) == 0
