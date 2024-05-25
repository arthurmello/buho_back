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
)

# temp qas
qas = []
vector_store = None


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


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


@app.post("/upload")
async def upload_files(files: List[UploadFile], directory = "./files/"):
    chunks = []
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
        else:
            print(f"File {file.filename} is not allowed skipping")

    tokens, embedding_cost = calculate_embedding_cost(chunks)
    
    print(f'Total Tokens: {tokens}')
    print(f'Embedding Cost in USD: {embedding_cost:.6f}')
    # vector store temp
    global vector_store
    vector_store = create_embeddings(chunks)
    return {"message": "Files uploaded successfully", "cost": embedding_cost}


class AskQuestionRequest(BaseModel):
    question: str
    owner: str


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
