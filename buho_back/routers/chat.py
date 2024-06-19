from fastapi import APIRouter
import os

from buho_back.models import AskQuestionRequest
from buho_back.config import settings
from buho_back.services.storage import dump_json, load_json, get_vector_store
from buho_back.services.answer import get_answer_and_sources

router = APIRouter()

data_directory = settings.DATA_DIRECTORY
chat_history_directory = settings.CHAT_HISTORY_DIRECTORY


def get_user_chat_history_file(user_id):
    return os.path.join(chat_history_directory, f"{user_id}.json")


@router.get("/history")
def get_chat_history(user_id: str = "user"):
    user_chat_history_file = get_user_chat_history_file(user_id)
    chat_history = load_json(user_chat_history_file)
    return {"chat_history": chat_history}


@router.get("/history/reset")
def reset_chat_history(user_id: str = "user"):
    user_chat_history_file = get_user_chat_history_file(user_id)
    try:
        os.remove(user_chat_history_file)
        result = {"message": "Chat history reset successfully"}
    except:
        result = {"message": "Chat history was already empty"}

    return result


@router.post("/ask")
async def ask_question(body: AskQuestionRequest, user_id: str = "user"):
    user_chat_history_file = get_user_chat_history_file(user_id)
    chat_history = load_json(user_chat_history_file)

    vector_store = get_vector_store(user_id)

    if vector_store:
        answer, sources = get_answer_and_sources(vector_store, body.question)
        chat_history.append(
            {
                "question": body.question,
                "answer": answer,
                "sources": sources,
                "owner": body.owner,
            }
        )
        dump_json(chat_history, user_chat_history_file)
    else:
        return {"error": "Please upload a file first"}

    return {"answer": answer, "sources": sources, "history": chat_history}
