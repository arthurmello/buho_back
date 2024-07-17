import os
import concurrent.futures
import uuid
import tiktoken

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from buho_back.services.storage.vectordb import VectorDbClient
from buho_back.services.storage.file_management import clear_directory
from buho_back.utils import ChatModel
from buho_back.config import settings


embedding_model = settings.EMBEDDING_MODEL
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY
chat_model = ChatModel()

extension_loaders = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader,
}


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013
    return 0, 0


def load_file(file):
    name, extension = os.path.splitext(file)
    try:
        loader = extension_loaders[extension](file)
    except:
        print("Document format is not supported!")
        return None

    print(f'Loading "{file}"')
    data = loader.load()
    for doc in data:
        doc.page_content = doc.page_content.replace("\n", " ")
    return data


# splitting data in chunks
def create_chunks(data, chunk_size=512, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(data)
    return chunks


# create embeddings and save them in a vector store
def create_vectordb(chunks, user_id):
    user_vectordb_directory = os.path.join(vectordb_directory, user_id)
    user_summaries_directory = os.path.join(summaries_directory, user_id)

    # reset database
    clear_directory(user_vectordb_directory)
    clear_directory(user_summaries_directory)

    vectordb_client = VectorDbClient(user_vectordb_directory)
    vectordb = vectordb_client.get_or_create_collection()
    documents = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [f"{uuid.uuid4()}" for _ in range(len(chunks))]
    vectordb.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Embeddings created on {user_vectordb_directory}.")
    return vectordb


def get_unique_files_from_chunks(chunks):
    return set([doc.metadata["source"].split("/")[-1] for doc in chunks])


def get_chunk_content_for_file(chunks, file):
    chunks = [
        chunk.page_content
        for chunk in chunks
        if chunk.metadata["source"].split("/")[-1] == file
    ]
    return chunks


def aggregate_chunks(chunks, max_size):
    aggregated_chunks = []
    current_chunk = ""

    for chunk in chunks:
        if len(current_chunk) + len(chunk) <= max_size:
            current_chunk = "\n".join([current_chunk, chunk])
        else:
            aggregated_chunks.append(current_chunk)
            current_chunk = chunk

    if current_chunk:  # Add the last chunk if it exists
        aggregated_chunks.append(current_chunk)

    return aggregated_chunks


@retry(
    wait=wait_random_exponential(min=15, max=65),
    stop=stop_after_attempt(5),
    reraise=True,
)
def summarize(text):
    prompt = f"summarize this in bullet points: {text}"
    answer = chat_model.invoke(prompt)
    return answer


def summarize_and_aggregate_chunks(chunks, max_size=400000):
    aggregated_chunks = aggregate_chunks(chunks, max_size=max_size)
    api_limit_tokens_per_minute = 30000
    number_of_chunks = len(aggregated_chunks)
    max_workers = int(number_of_chunks * max_size / api_limit_tokens_per_minute)
    print(f"{number_of_chunks=}")
    print(f"{max_workers=}")
    while len(aggregated_chunks) > 1 or (
        len(aggregated_chunks) == 1 and len(aggregated_chunks[0]) > max_size
    ):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            summarized_chunks = list(executor.map(summarize, aggregated_chunks))
        aggregated_chunks = aggregate_chunks(summarized_chunks, max_size=max_size)
    return aggregated_chunks[0]


def create_summaries(chunks, user_id):
    user_summaries_directory = os.path.join(summaries_directory, user_id)
    print("Creating summaries...")
    clear_directory(user_summaries_directory)
    if not os.path.exists(user_summaries_directory):
        os.makedirs(user_summaries_directory)

    files = get_unique_files_from_chunks(chunks)

    for file in files:
        filename = file.split(".")[0]
        print(f"... for file {filename}")
        file_chunks = get_chunk_content_for_file(chunks, file)
        file_summary = summarize_and_aggregate_chunks(file_chunks)
        with open(f"{user_summaries_directory}/{filename}.txt", "w+") as text_file:
            text_file.write(file_summary)

    print(f"Summaries created on {user_summaries_directory}.")
