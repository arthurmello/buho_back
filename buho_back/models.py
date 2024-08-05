from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str
    owner: str


class OutputFileRequest(BaseModel):
    filename: str
    user_parameters: dict | None = None


class CreateDealRequest(BaseModel):
    deal: str


class DeleteDealRequest(BaseModel):
    deal: str


class MoveRequest(BaseModel):
    originPath: str
    destinationPath: str
