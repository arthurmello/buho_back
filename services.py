from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_experimental.text_splitter import SemanticChunker
from langchain.chains import RetrievalQA
import tiktoken
import os
from dotenv import load_dotenv
import shutil

load_dotenv()
openai_api_key=os.environ['OPENAI_API_KEY']
embedding_model = "text-embedding-3-large"
embeddings = OpenAIEmbeddings(
        model=embedding_model, openai_api_key=openai_api_key
    )

def clear_directory(directory):
    if os.path.exists(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
            print(f"{directory} cleared!")


# loading PDF, DOCX and TXT files as LangChain Documents
def load_document(file):
    import os

    name, extension = os.path.splitext(file)

    if extension == ".pdf":
        loader = PyPDFLoader(file)
    elif extension == ".docx":
        loader = Docx2txtLoader(file)
    elif extension == ".txt":
        loader = TextLoader(file)
    else:
        print("Document format is not supported!")
        return None
    
    print(f'Loading "{file}"')
    data = loader.load()
    for doc in data:
        doc.page_content = doc.page_content.replace('\n', ' ')
    return data


# splitting data in chunks
def chunk_data(data, chunk_size=1024, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(data)
    return chunks

    
# create embeddings using OpenAIEmbeddings() and save them in a Chroma vector store
def create_embeddings(chunks, persist_directory="./mychroma_db"):

    # reset database
    clear_directory(persist_directory)
    
    # if you want to use a specific directory for chromadb
    vector_store = Chroma.from_documents(
        chunks, embeddings, persist_directory=persist_directory
    )
    print(f"Embeddings created on {persist_directory}.")
    return vector_store

def ask_and_get_answer(vector_store, q, k=10):

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold", search_kwargs={"k": k, "score_threshold": 0.4}
    )
    # for doc in vector_store.similarity_search_with_score(q, k):
    #     print(doc)

    chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever,
        chain_type_kwargs={"verbose": True},
        return_source_documents=True
    )
    answer = chain.invoke(q)

    result = answer['result'],
    sources = [{
            "page_content": doc.page_content,
            "file": doc.metadata.get('source').split('/')[-1],
            "page": doc.metadata.get('page', '-')
            } for doc in answer['source_documents']]
    
    return result, sources 


# calculate embedding cost using tiktoken
def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page.page_content)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013
