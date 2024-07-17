import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Environment variables
    OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

    # Hard-coded settings
    DATA_DIRECTORY: str = os.path.join(".", "buho_back", "_data")
    TEMPLATES_DIRECTORY: str = os.path.join(".", "buho_back", "templates")
    INSTRUCTIONS_DIRECTORY: str = os.path.join(".", "buho_back", "instructions")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM: str = "gpt-4o"
    N_SOURCES_TO_DISPLAY: int = 3

    @property
    def VECTORDB_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/vector_db"

    @property
    def SUMMARIES_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/summaries"

    @property
    def INPUT_FILES_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/input_files"

    @property
    def OUTPUT_FILES_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/output_files"

    @property
    def CHAT_HISTORY_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/chat_history"

    @property
    def QA_TRACKER_DIRECTORY(self):
        return f"{self.DATA_DIRECTORY}/qa_tracker"


settings = Settings()
