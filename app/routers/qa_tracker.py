from fastapi import APIRouter
from ..models import AskQuestionRequest
from ..config import settings
from ..services.storage import dump_json, load_json

qa_tracker_file = settings.QA_TRACKER_FILE
qa_tracker = load_json(qa_tracker_file)

router = APIRouter()

@router.get("/")
def get_qa_tracker():
    qa_tracker = load_json(qa_tracker_file)
    return {"qa_tracker": qa_tracker}

@router.get("/reset")
def reset_qa_tracker():
    qa_tracker = []
    dump_json(qa_tracker, qa_tracker_file)
    return {"message": "QA tracker reset successfully"}

@router.post("/add")
async def add_question_to_qa_tracker(body: AskQuestionRequest):
    qa_tracker.append({"question": body.question, "owner": body.owner})
    dump_json(qa_tracker, qa_tracker_file)
    return {"message": "Question added successfully"}