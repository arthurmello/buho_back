import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


# class Settings(BaseSettings):
# Environment variables
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

# Hard-coded settings
DATA_DIRECTORY: str = os.path.join(".", "buho_back", "_data")
TEMPLATES_DIRECTORY: str = os.path.join(
    ".", "buho_back", "services", "file_generation", "templates"
)
INSTRUCTIONS_DIRECTORY: str = os.path.join(
    ".", "buho_back", "services", "file_generation", "instructions"
)
EMBEDDING_MODEL: str = "text-embedding-3-small"
LLM: str = "gpt-4o"
N_SOURCES_TO_DISPLAY: int = 3

# settings = Settings()


# @property
def vectordb_directory(deal, user):
    # return f"{self.DATA_DIRECTORY}/vectordb"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "vectordb")


# @property
def summaries_directory(deal, user):
    # return f"{self.DATA_DIRECTORY}/summaries"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "summaries")


# @property
def input_files_directory(deal, user):
    # return f"{self.DATA_DIRECTORY}/input_files"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "input_files")


# @property
def output_files_directory(deal, user):
    # return f"{self.DATA_DIRECTORY}/output_files"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "output_files")


# @property
def chat_history_file(deal, user):
    # return f"{self.DATA_DIRECTORY}/chat_history"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "chat_history.json")


# @property
def qa_tracker_directory(deal, user):
    # return f"{self.DATA_DIRECTORY}/qa_tracker"
    return os.path.join(f"{DATA_DIRECTORY}", deal, user, "qa_tracker")
