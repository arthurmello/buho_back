from buho_back.services.context import create_general_context, concatenate_chunks
from buho_back.services.retriever import retrieve_chunks
from buho_back.config import settings
from buho_back.utils import chat_model

n_sources_to_display = settings.N_SOURCES_TO_DISPLAY


def format_question_with_full_context(general_context, chunk_context, question):
    question_with_full_context = f"{general_context} +\
        Here's some specific context: {chunk_context}. + \
        Now, answer this question: {question}"
    return question_with_full_context


def get_answer_and_sources(vector_store, question, k=10):
    general_context = create_general_context()
    source_chunks = retrieve_chunks(vector_store, question)
    chunk_context = concatenate_chunks(source_chunks)
    question_with_full_context = format_question_with_full_context(
        general_context, chunk_context, question
    )

    answer = chat_model.invoke(question_with_full_context)

    result = answer.content
    sources = [
        {
            "page_content": doc.page_content,
            "file": doc.metadata.get("source").split("/")[-1],
            "page": doc.metadata.get("page", "-"),
        }
        for doc in source_chunks
    ][:n_sources_to_display]

    return result, sources
