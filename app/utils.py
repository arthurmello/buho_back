import tiktoken
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.config import settings

openai_api_key = settings.OPENAI_API_KEY
llm = settings.LLM
embedding_model = settings.EMBEDDING_MODEL


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page.page_content)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013


embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openai_api_key)

chat_model = ChatOpenAI(model=llm, temperature=0)
