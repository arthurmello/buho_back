import os

from buho_back.config import N_SOURCES_TO_DISPLAY, HYBRID_SEARCH_PARAMS
from buho_back.services.storage.file_management import get_summaries_directory
from buho_back.utils import ChatModel, concatenate_chunks

chat_model = ChatModel()


def create_general_context(summaries_directory):
    context = """You are an investment banking associate, working on a specific financial deal.
        You'll be given some file summaries, as well as some other relevant information.
        Your goal is to answer questions related to the financial deal,
        based on the files and on the other information provided.
        Do not mention the summaries of the files, just the files themselves.
        Here's a summary of all the files made available to you: /n"""
    for filename in os.listdir(summaries_directory):
        if os.path.isfile(os.path.join(summaries_directory, filename)):
            with open(os.path.join(summaries_directory, filename), "r") as file:
                summary_content = file.read()
            context += f'"{filename}":\n"{summary_content}"\n\n'
    return context


def format_question_with_full_context(general_context, chunk_context, question):
    question_with_full_context = f"""{general_context} +\
        Here's some specific context: {chunk_context}. + \
        Now, answer this question: {question}
        Your answer should be in plain text.
        Do not use LaTeX nor Markdown.
        """
    return question_with_full_context


def get_answer_and_sources(vectordb, question, user, deal):
    summaries_directory = get_summaries_directory(user, deal)
    general_context = create_general_context(summaries_directory)
    source_chunks = vectordb.retrieve_chunks(text=question, params=HYBRID_SEARCH_PARAMS)
    chunk_context = concatenate_chunks(source_chunks)
    question_with_full_context = format_question_with_full_context(
        general_context, chunk_context, question
    )

    result = chat_model.invoke(question_with_full_context)

    sources = [
        {
            "page_content": doc["document"],
            "file": doc["metadata"].get("source").split("/")[-1],
            "page": doc["metadata"].get("page", "-"),
        }
        for doc in source_chunks
    ][:N_SOURCES_TO_DISPLAY]

    return result, sources
