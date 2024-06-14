# app/config.py
import os
import json
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Get the directory of the current script file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

# Load the config.json file
with open(config_path) as config_file:
    config_data = json.load(config_file)

data_directory = config_data["data_directory"]
for var in ["vectordb_directory", "summaries_directory", "files_directory", "chat_history_file", "qa_tracker_file"]:
    config_data[var] = config_data[var].format(data_directory=data_directory)

class Settings(BaseSettings):
    # Environment variables
    OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

    # Hard-coded settings from config.json
    EMBEDDING_MODEL: str = config_data["embedding_model"]
    VECTORDB_DIRECTORY: str = config_data["vectordb_directory"]
    SUMMARIES_DIRECTORY: str = config_data["summaries_directory"]
    FILES_DIRECTORY: str = config_data["files_directory"]
    CHAT_HISTORY_FILE: str = config_data["chat_history_file"]
    QA_TRACKER_FILE: str = config_data["qa_tracker_file"]
    LLM: str = config_data["llm"]
    N_SOURCES_TO_DISPLAY: int = config_data["n_sources_to_display"]

# Create an instance of the Settings class
settings = Settings()