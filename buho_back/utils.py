import ast
import re
from openai import OpenAI
from buho_back.config import OPENAI_API_KEY, LLM

client = OpenAI(api_key=OPENAI_API_KEY)


class ChatModel:
    def __init__(self, model=LLM, temperature=0):
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


def extract_url(text):
    url_pattern = r"https?://[^\s/$.?#].[^\s]*"
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    else:
        return None


def extract_dict(text):
    pattern = r"\{.*\}"
    match = re.search(pattern, text, re.DOTALL)
    try:
        text = match.group(0).strip()
        return ast.literal_eval(text)
    except Exception as e:
        print(f"Error extracting dict: {e}")
        return None
