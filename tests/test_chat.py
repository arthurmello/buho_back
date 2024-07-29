import json
import pytest
from fastapi.testclient import TestClient
import ast
import numpy as np
import os
import time

from buho_back.main import app
from buho_back.utils import ChatModel

current_dir = os.path.dirname(os.path.abspath(__file__))
client = TestClient(app)
user = "test_user"

file_for_test = "file_for_test.pdf"
file_path = os.path.join(current_dir, file_for_test)
files = [("files", open(file_path, "rb"))]

qa_file_name = "questions_answers_for_test.json"
qa_file_path = os.path.join(current_dir, qa_file_name)

chat_model = ChatModel()


@pytest.fixture(scope="session", autouse=True)
def cleanup_and_upload():
    # Cleanup before running tests
    client.get(f"/input_files/reset?user={user}")

    # Upload test file
    response_from_upload = client.post(f"/input_files/upload?user={user}", files=files)

    if response_from_upload.status_code == 200:
        print("Files uploaded successfully!")
    else:
        print("Error uploading files...")

    yield

    # Cleanup after running tests
    client.get(f"/input_files/reset?user={user}")


def test_ask_question_and_get_chat_history():
    test_question = "summarize this file"
    body = {"question": test_question, "owner": "test_user"}
    response_from_ask = client.post(f"/chat/ask?user={user}", content=json.dumps(body))
    assert response_from_ask.status_code == 200
    assert "error" not in response_from_ask.json().keys()
    assert "answer" in response_from_ask.json().keys()
    assert "sources" in response_from_ask.json().keys()
    assert "history" in response_from_ask.json().keys()

    response_from_chat_history = client.get(f"/chat/history/?user={user}")
    assert response_from_chat_history.status_code == 200

    chat_history = response_from_chat_history.json()["chat_history"]
    chat_history_questions = [item["question"] for item in chat_history]
    assert test_question in chat_history_questions

    response_from_chat_history_reset = client.get(f"/chat/history/reset?user={user}")
    assert response_from_chat_history_reset.status_code == 200

    response_from_chat_history = client.get(f"/chat/history/?user={user}")
    chat_history = response_from_chat_history.json()["chat_history"]
    chat_history_questions = [item["question"] for item in chat_history]
    assert len(chat_history_questions) == 0


def test_answer_quality(evaluation_threshold=0.5):

    with open(qa_file_path) as f:
        questions_and_answers = json.load(f)

    def evaluate_answer(question, expected_answer, answer_to_evaluate):
        prompt = f"""
            Evaluate if the answer given to a question is correct:
            1 means a correct answer
            0 means an incorrect answer

            Here's the question: {question}
            Here's the expected answer: {expected_answer}
            Here's the answer you need to evaluate: {answer_to_evaluate}

            Don't add any text to your response, just answer with a number (0 or 1).
        """
        evaluation = chat_model.invoke(prompt)
        return evaluation

    evaluations = []

    for qa in questions_and_answers:
        question = qa["question"]
        expected_answer = qa["answer"]
        print(f"{question=}")
        print(f"{expected_answer=}")

        body = {"question": question, "owner": "test_user"}
        response_from_ask = client.post(
            f"/chat/ask?user={user}", content=json.dumps(body)
        )
        if "answer" in response_from_ask.json().keys():
            answer_to_evaluate = response_from_ask.json()["answer"]
            print(response_from_ask.json()["sources"])
            evaluation = ast.literal_eval(
                evaluate_answer(question, expected_answer, answer_to_evaluate)
            )
            print(f"{answer_to_evaluate=}")
            print(f"{evaluation=}")
        else:
            print("error")
            evaluation = 0

        evaluations.append(evaluation)
    average_evaluation = np.mean(evaluations)
    print(f"{average_evaluation=}")
    assert (
        average_evaluation > evaluation_threshold
    ), f"Average evaluation is below the threshold ({evaluation_threshold})"
