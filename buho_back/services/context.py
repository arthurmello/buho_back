import os
from buho_back.config import settings

summaries_directory = settings.SUMMARIES_DIRECTORY


def create_general_context(directory=summaries_directory):
    context = """You are an investment banking associate, working on a specific financial deal.
        You'll be given some file summaries, as well as some other relevant information.
        Your goal is to answer questions related to the financial deal,
        based on the files and on the other information provided.
        Do not mention the summaries of the files, just the files themselves.
        Here's a summary of all the files made available to you: /n"""
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            with open(os.path.join(directory, filename), "r") as file:
                summary_content = file.read()
            context += f'"{filename}":\n"{summary_content}"\n\n'
    return context


def concatenate_chunks(chunks):
    chunk_context = "\n".join([doc.page_content for doc in chunks])
    return chunk_context
