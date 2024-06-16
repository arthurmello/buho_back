from fastapi import APIRouter
from buho_back.services.answer import get_answer_and_sources
from buho_back.models import AskQuestionRequest
from buho_back.config import settings
from buho_back.services.storage import dump_json, load_json, get_vector_store

router = APIRouter()

chat_history_file = settings.CHAT_HISTORY_FILE
chat_history = load_json(chat_history_file)


@router.get("/history")
def get_chat_history():
    chat_history = load_json(chat_history_file)
    return {"chat_history": chat_history}


@router.get("/history/reset")
def reset_chat_history():
    chat_history = []
    dump_json(chat_history, chat_history_file)

    return {"message": "Chat history reset successfully"}


@router.post("/ask")
async def ask_question(body: AskQuestionRequest):
    vector_store = get_vector_store()

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
        dump_json(chat_history, chat_history_file)
    else:
        return {"error": "Please upload a file first"}

    return {"answer": answer, "sources": sources, "history": chat_history}
