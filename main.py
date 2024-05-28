from fastapi import FastAPI
from fastapi import UploadFile, File
from typing import List
import os
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from services import (
    ask_and_get_answer,
    calculate_embedding_cost,
    chunk_data,
    create_embeddings,
    load_document,
    clear_directory
)

# temp qas
qas = []
qas_tracker = []
vector_store = None
files_directory = "./files/"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class AskQuestionRequest(BaseModel):
    question: str
    owner: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/qas")
def get_qas():
    return {"qas": qas}


@app.get("/qas/reset")
def reset_qas():
    global qas
    qas = []
    global vector_store
    vector_store = None
    return {"message": "QAs reset successfully"}


@app.get("/qas_tracker")
def get_qas_tracker():
    return {"qas_tracker": qas_tracker}


@app.get("/qas_tracker/reset")
def reset_qas_tracker():
    global qas_tracker
    qas_tracker = []
    return {"message": "QAs tracker reset successfully"}

@app.post("/qas_tracker/add")
async def add_question_to_qas_tracker(body: AskQuestionRequest):
    qas_tracker.append({"question": body.question, "owner": body.owner})
    
    return {"message": "Question added successfully"}


@app.post("/upload")
async def upload_files(files: List[UploadFile], directory = files_directory):
    chunks = []
    clear_directory(directory) #this first clear is for safety, just in case there were some remaining files
    if not os.path.exists(directory):
        os.makedirs(directory)

    for file in files:
        # Check if the file extension is allowed
        allowed_extensions = [".pdf", ".txt", ".docx"]
        if file.filename.endswith(tuple(allowed_extensions)):
            # Call the load_document function from services
            bytes_data = file.file.read()
            file_name = os.path.join(directory, file.filename)
            # Save the file locally
            with open(file_name, "wb") as f:
                f.write(bytes_data)
            data = load_document(file_name)
            chunks.extend(chunk_data(data))
            print(f'Chunks for "{file.filename}" created.')
        else:
            print(f'File "{file.filename}" extension is not supported. Supported extensions: {allowed_extensions}')

    tokens, embedding_cost = calculate_embedding_cost(chunks)
    
    print(f'Total Tokens: {tokens}')
    print(f'Embedding Cost in USD: {embedding_cost:.6f}')
    # vector store temp
    global vector_store
    vector_store = create_embeddings(chunks)
    clear_directory(directory) # we clear the directory twice to avoid cluttering
    return {"message": "Files uploaded successfully", "cost": embedding_cost}

@app.get("/files/list")
async def list_files():
    if vector_store:
        files_list = [
            name.split('/')[-1] for name in set(
                [meta["source"] for meta in vector_store.get()["metadatas"]]
                )
            ]
        files = [{"name":file} for file in files_list]
    else:
        files = []
    return files

@app.post("/ask")
async def ask_question(body: AskQuestionRequest):
    if vector_store:
        answer, sources = ask_and_get_answer(vector_store, body.question)
        qas.append({"question": body.question, "answer": answer, "sources": sources, "owner": body.owner})
    else:
        return {"error": "Please upload a file first"}

    return {"answer": answer, "sources": sources, "history": qas}


if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=8080, timeout_keep_alive=600, forwarded_allow_ips="*"
    )
