from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str
    owner: str


class OutputFileRequest(BaseModel):
    filename: str
