from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str
    owner: str


class OutputFileRequest(BaseModel):
    filename: str


class Document(BaseModel):
    id: str
    page_content: str
    metadata: dict
