import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
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
CHUNKING_PARAMS: dict = {"chunk_size": 512, "chunk_overlap": 100}
HYBRID_SEARCH_PARAMS = {
    "k_for_semantic_search": 5,
    "alpha_for_hybrid_search": 0.1,
    "k_for_hybrid_search": 5,
    "distance_threshold": None,
}
