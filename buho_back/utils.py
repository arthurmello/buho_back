import tiktoken
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from buho_back.config import settings

openai_api_key = settings.OPENAI_API_KEY
llm = settings.LLM
embedding_model = settings.EMBEDDING_MODEL

client = OpenAI(api_key=openai_api_key)


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page.page_content)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013


embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openai_api_key)


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
