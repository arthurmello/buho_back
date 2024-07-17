import tiktoken
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.config import Settings
from openai import OpenAI
from buho_back.config import settings


openai_api_key = settings.OPENAI_API_KEY
llm = settings.LLM
embedding_model = settings.EMBEDDING_MODEL

client = OpenAI(api_key=openai_api_key)


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013
    return 0, 0


class ChromaClient:
    def __init__(self, path):
        self.path = path
        self.chroma_client = chromadb.PersistentClient(
            path=path, settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=openai_api_key, model_name=embedding_model
        )
        self.collection_name = "collection"
        self.chroma_client.clear_system_cache()

    def create_collection(self):
        return self.chroma_client.create_collection(
            name=self.collection_name, embedding_function=self.embedding_function
        )

    def get_collection(self):
        return self.chroma_client.get_collection(
            name=self.collection_name, embedding_function=self.embedding_function
        )

    def get_or_create_collection(self):
        return self.chroma_client.get_or_create_collection(
            name=self.collection_name, embedding_function=self.embedding_function
        )


class ChatModel:
    def __init__(self, model=llm, temperature=0):
        self.model = model
        self.temperature = temperature

    def invoke(self, prompt):
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content
