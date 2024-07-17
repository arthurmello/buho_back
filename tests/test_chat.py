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


def test_ask_question_and_get_chat_history():
    file_for_test = "file_for_test.pdf"
    file_path = os.path.join(current_dir, file_for_test)
    files = [("files", open(file_path, "rb"))]
    response_from_upload = client.post(
        f"/input_files/upload?user_id={user}", files=files
    )

    test_question = "summarize this file"
    body = {"question": test_question, "owner": "test_user"}
    response_from_ask = client.post(
        f"/chat/ask?user_id={user}", content=json.dumps(body)
    )
    assert response_from_ask.status_code == 200
    assert "error" not in response_from_ask.json().keys()
    assert "answer" in response_from_ask.json().keys()
    assert "sources" in response_from_ask.json().keys()
    assert "history" in response_from_ask.json().keys()

    response_from_chat_history = client.get(f"/chat/history/?user_id={user}")
    assert response_from_chat_history.status_code == 200

    chat_history = response_from_chat_history.json()["chat_history"]
    chat_history_questions = [item["question"] for item in chat_history]
    assert test_question in chat_history_questions

    response_from_chat_history_reset = client.get(f"/chat/history/reset?user_id={user}")
    assert response_from_chat_history_reset.status_code == 200

    response_from_chat_history = client.get(f"/chat/history/?user_id={user}")
    chat_history = response_from_chat_history.json()["chat_history"]
    chat_history_questions = [item["question"] for item in chat_history]
    assert len(chat_history_questions) == 0
