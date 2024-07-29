import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

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
