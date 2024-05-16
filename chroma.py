# create the chroma client
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

client = chromadb.HttpClient(settings=Settings(allow_reset=True))
client.reset()  # resets the database
collection = client.create_collection("my_collection")

# tell LangChain to use our client and collection name
db = Chroma(
    client=client,
    collection_name="my_collection",
    embedding_function=OpenAIEmbeddings(
        model="text-embedding-3-small", dimensions=1536
    ),
)


def add_document(file_name, doc):
    collection.add(ids=[file_name], metadatas=doc.metadata, documents=doc.page_content)


def get_chroma_db():
    return db
