import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

from buho_back.utils import chat_model, embeddings
from buho_back.config import settings
from buho_back.services.storage import clear_directory
from buho_back.services.chains import map_reduce_setup

embedding_model = settings.EMBEDDING_MODEL
vectordb_directory = settings.VECTORDB_DIRECTORY
summaries_directory = settings.SUMMARIES_DIRECTORY
extension_loaders = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader,
}


# loading PDF, DOCX and TXT files as LangChain Documents
def load_document(file):
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
def create_chunks(data, chunk_size=1024, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(data)
    return chunks


# create embeddings and save them in a vector store
def create_vector_store(chunks):

    # reset database
    clear_directory(vectordb_directory)
    clear_directory(summaries_directory)

    vector_store = Chroma.from_documents(
        chunks, embeddings, persist_directory=vectordb_directory
    )
    print(f"Embeddings created on {vectordb_directory}.")
    return vector_store


def create_summaries(chunks, directory=summaries_directory):
    print("Creating summaries...")
    clear_directory(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)

    map_reduce_chain = map_reduce_setup(chat_model)

    files = set([doc.metadata["source"].split("/")[-1] for doc in chunks])

    for file in files:
        file_chunks = [
            chunk for chunk in chunks if chunk.metadata["source"].split("/")[-1] == file
        ]
        result = map_reduce_chain.invoke(file_chunks)
        file_summary = result["output_text"]
        file_name = file.split(".")[0]
        with open(f"{directory}/{file_name}.txt", "w+") as text_file:
            text_file.write(file_summary)

    print(f"Summaries created on {directory}.")
