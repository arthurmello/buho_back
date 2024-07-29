from fastapi import APIRouter
import os

from buho_back.models import AskQuestionRequest
from buho_back.services.storage.file_management import (
    dump_json,
    load_json,
    get_chat_history_file,
)
from buho_back.services.storage.vectordb import get_vectordb
from buho_back.services.answer import get_answer_and_sources

router = APIRouter()


@router.get("/history")
def get_chat_history(user: str = "user", deal: str = "deal"):
    chat_history_file = get_chat_history_file(user, deal)
    chat_history = load_json(chat_history_file)
    return {"chat_history": chat_history}


@router.get("/history/reset")
def reset_chat_history(user: str = "user", deal: str = "deal"):
    chat_history_file = get_chat_history_file(user, deal)
    try:
        os.remove(chat_history_file)
        result = {"message": "Chat history reset successfully"}
    except:
        result = {"message": "Chat history was already empty"}

    return result


@router.post("/ask")
async def ask_question(
    body: AskQuestionRequest, user: str = "user", deal: str = "deal"
):
    chat_history_file = get_chat_history_file(user, deal)
    chat_history = load_json(chat_history_file)

    vectordb = get_vectordb(user, deal)

    if vectordb:
        answer, sources = get_answer_and_sources(vectordb, body.question, user, deal)
        chat_history.append(
            {
                "question": body.question,
                "answer": answer,
                "sources": sources,
                "owner": body.owner,
            }
        )
        dump_json(chat_history, chat_history_file)
    else:
        return {"error": "Please upload a file first"}

    return {"answer": answer, "sources": sources, "history": chat_history}
