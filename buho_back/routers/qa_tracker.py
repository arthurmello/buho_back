from fastapi import APIRouter
from buho_back.models import AskQuestionRequest
from buho_back.config import settings
from buho_back.services.storage import dump_json, load_json

qa_tracker_file = settings.QA_TRACKER_FILE
qa_tracker = load_json(qa_tracker_file)

router = APIRouter()


@router.get("/")
def get_qa_tracker():
    global qa_tracker
    qa_tracker = load_json(qa_tracker_file)
    return {"qa_tracker": qa_tracker}


@router.get("/reset")
def reset_qa_tracker():
    global qa_tracker
    qa_tracker = []
    dump_json(qa_tracker, qa_tracker_file)
    return {"message": "QA tracker reset successfully"}


@router.post("/add")
async def add_question_to_qa_tracker(body: AskQuestionRequest):
    global qa_tracker
    qa_tracker = load_json(qa_tracker_file)
    qa_tracker.append({"question": body.question, "owner": body.owner})
    dump_json(qa_tracker, qa_tracker_file)
    return {"message": "Question added successfully"}
