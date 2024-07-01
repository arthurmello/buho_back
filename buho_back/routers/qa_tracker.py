from fastapi import APIRouter
import os
from buho_back.models import AskQuestionRequest
from buho_back.config import settings
from buho_back.services.storage import dump_json, load_json

qa_tracker_directory = settings.QA_TRACKER_DIRECTORY
data_directory = settings.DATA_DIRECTORY

router = APIRouter()


def get_user_qa_tracker_file(user_id):
    return os.path.join(qa_tracker_directory, f"{user_id}.json")


@router.get("/")
def get_qa_tracker(user_id: str = "user"):
    user_qa_tracker_file = get_user_qa_tracker_file(user_id)
    qa_tracker = load_json(user_qa_tracker_file)
    return {"qa_tracker": qa_tracker}


@router.get("/reset")
def reset_qa_tracker(user_id: str = "user"):
    user_qa_tracker_file = get_user_qa_tracker_file(user_id)
    try:
        os.remove(user_qa_tracker_file)
        result = {"message": "QA tracker reset successfully"}
    except:
        result = {"message": "QA tracker was already empty"}
    return result


@router.post("/add")
async def add_question_to_qa_tracker(body: AskQuestionRequest, user_id: str = "user"):
    user_qa_tracker_file = get_user_qa_tracker_file(user_id)
    qa_tracker = load_json(user_qa_tracker_file)
    qa_tracker.append({"question": body.question, "owner": body.owner})
    dump_json(qa_tracker, user_qa_tracker_file)
    return {"message": "Question added successfully"}
