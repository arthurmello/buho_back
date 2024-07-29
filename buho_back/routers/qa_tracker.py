from fastapi import APIRouter
import os
from buho_back.models import AskQuestionRequest
from buho_back.services.storage.file_management import (
    dump_json,
    load_json,
    get_qa_tracker_directory,
)


router = APIRouter()


def get_user_qa_tracker_file(deal: str = "deal", user: str = "user"):

    return os.path.join(get_qa_tracker_directory(deal, user), f"{user}.json")


@router.get("/")
def get_qa_tracker(deal: str = "deal", user: str = "user"):
    user_qa_tracker_file = get_user_qa_tracker_file(deal, user)
    qa_tracker = load_json(user_qa_tracker_file)
    return {"qa_tracker": qa_tracker}


@router.get("/reset")
def reset_qa_tracker(deal: str = "deal", user: str = "user"):
    user_qa_tracker_file = get_user_qa_tracker_file(deal, user)
    try:
        os.remove(user_qa_tracker_file)
        result = {"message": "QA tracker reset successfully"}
    except:
        result = {"message": "QA tracker was already empty"}
    return result


@router.post("/add")
async def add_question_to_qa_tracker(
    body: AskQuestionRequest, deal: str = "deal", user: str = "user"
):
    user_qa_tracker_file = get_user_qa_tracker_file(deal, user)
    qa_tracker = load_json(user_qa_tracker_file)
    qa_tracker.append({"question": body.question, "owner": body.owner})
    dump_json(qa_tracker, user_qa_tracker_file)
    return {"message": "Question added successfully"}
