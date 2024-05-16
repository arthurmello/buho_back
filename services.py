from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key=os.environ['OPENAI_API_KEY']

# loading PDF, DOCX and TXT files as LangChain Documents
def load_document(file):
    import os

    name, extension = os.path.splitext(file)

    if extension == ".pdf":
        print(f"Loading {file}")
        loader = PyPDFLoader(file)
    elif extension == ".docx":
        print(f"Loading {file}")
        loader = Docx2txtLoader(file)
    elif extension == ".txt":
        loader = TextLoader(file)
    else:
        print("Document format is not supported!")
        return None

    data = loader.load()
    return data


# splitting data in chunks
def chunk_data(data, chunk_size=256, chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(data)
    return chunks


# create embeddings using OpenAIEmbeddings() and save them in a Chroma vector store
def create_embeddings(chunks):
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", dimensions=1536, openai_api_key=openai_api_key
    )  # 512 works as well
    # vector_store = Chroma.from_documents(chunks, embeddings)

    # if you want to use a specific directory for chromadb
    vector_store = Chroma.from_documents(
        chunks, embeddings, persist_directory="./mychroma_db"
    )
    return vector_store


def ask_and_get_answer(vector_store, q, k=3):

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=1)
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": k}
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever
    )

    answer = chain.invoke(q)
    return answer["result"]


# calculate embedding cost using tiktoken
def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model("text-embedding-3-small")
    total_tokens = sum([len(enc.encode(page.page_content)) for page in texts])
    # check prices here: https://openai.com/pricing
    # print(f'Total Tokens: {total_tokens}')
    # print(f'Embedding Cost in USD: {total_tokens / 1000 * 0.00002:.6f}')
    return total_tokens, total_tokens / 1000 * 0.00002
