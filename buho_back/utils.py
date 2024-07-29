from openai import OpenAI
from buho_back.config import OPENAI_API_KEY, LLM

openai_api_key = OPENAI_API_KEY
llm = LLM
client = OpenAI(api_key=openai_api_key)


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


def concatenate_chunks(chunks):
    documents = [chunk["document"] for chunk in chunks]
    chunk_context = "\n".join(documents)
    return chunk_context


def safe_cast(value):
    try:
        return float(value)
    except ValueError:
        return value
