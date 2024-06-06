from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_experimental.text_splitter import SemanticChunker

from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.combine_documents.reduce import ReduceDocumentsChain
from langchain.chains.llm import LLMChain
# from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


from openai import OpenAI
import tiktoken
import os
from dotenv import load_dotenv
import shutil

load_dotenv()
openai_api_key=os.environ['OPENAI_API_KEY']
embedding_model = "text-embedding-3-small"
persist_directory="./mychroma_db"
summaries_directory="./summaries"
embeddings = OpenAIEmbeddings(
        model=embedding_model, openai_api_key=openai_api_key
    )

def clear_directory(directory=persist_directory):
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
def create_embeddings(chunks, persist_directory=persist_directory):

    # reset database
    clear_directory(persist_directory)
    clear_directory(summaries_directory)
    
    # if you want to use a specific directory for chromadb
    vector_store = Chroma.from_documents(
        chunks, embeddings, persist_directory=persist_directory
    )
    print(f"Embeddings created on {persist_directory}.")
    return vector_store

def create_general_context(directory=summaries_directory):
    context = """You are an investment banking associate, working on a specific financial deal.
        You'll be given some file summaries, as well as some other relevant information.
        Your goal is to answer questions related to the financial deal,
        based on the files and on the other information provided.
        Do not mention the summaries of the files, just the files themselves.
        Here's a summary of all the files made available to you: /n"""
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            with open(os.path.join(directory, filename), 'r') as file:
                summary_content = file.read()
            context += f'"{filename}":\n"{summary_content}"\n\n'
    return context

def retrieve_chunks(vector_store, question, k=10):
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold", search_kwargs={"k": k, "score_threshold": -0.1}
    )
    chunks = retriever.invoke(question)
    return chunks

def format_question_with_full_context(general_context, chunk_context, question):
    question_with_full_context = f"{general_context} +\
        Here's some specific context: {chunk_context}. + \
        Now, answer this question: {question}"
    return question_with_full_context

def ask_and_get_answer(vector_store, question, k=10):
    n_sources_to_display=3
    general_context = create_general_context()
    source_chunks = retrieve_chunks(vector_store, question)
    chunk_context = "\n".join([doc.page_content for doc in source_chunks])
    question_with_full_context = format_question_with_full_context(general_context, chunk_context, question)
    
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    answer = llm.invoke(question_with_full_context)
    
    result = answer.content
    sources = [{
            "page_content": doc.page_content,
            "file": doc.metadata.get('source').split('/')[-1],
            "page": doc.metadata.get('page', '-')
            } for doc in source_chunks][:n_sources_to_display]
    
    return result, sources 


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(embedding_model)
    total_tokens = sum([len(enc.encode(page.page_content)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013

def summarize_text(text, summary_length=100):
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": f"Summarize this in less than {summary_length} words:."},
        {"role": "user", "content": text}
    ]
    )

    result = completion.choices[0].message.content
    return result

def create_summaries(chunks, directory=summaries_directory):
    print("Creating summaries...")
    clear_directory(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    llm = ChatOpenAI(temperature=0)

    # Map
    map_template = """The following is a set of documents
    {docs}
    Based on this list of docs, please summarize them into bullet points.
    Helpful Answer:"""
    map_prompt = ChatPromptTemplate.from_template(map_template)
    map_chain = LLMChain(llm=llm, prompt=map_prompt)

    # Reduce
    reduce_template = """The following is set of summaries:
    {docs}
    Take these and distill it into a final, consolidated summary, using bullet points. 
    Helpful Answer:"""
    reduce_prompt = ChatPromptTemplate.from_template(reduce_template)
    reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)

    # Takes a list of documents, combines them into a single string, and passes this to an LLMChain
    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_chain, document_variable_name="docs"
    )

    # Combines and iteratively reduces the mapped documents
    reduce_documents_chain = ReduceDocumentsChain(
        # This is final chain that is called.
        combine_documents_chain=combine_documents_chain,
        # If documents exceed context for `StuffDocumentsChain`
        collapse_documents_chain=combine_documents_chain,
        # The maximum number of tokens to group documents into.
        token_max=4000,
    )

    # Combining documents by mapping a chain over them, then combining results
    map_reduce_chain = MapReduceDocumentsChain(
        # Map chain
        llm_chain=map_chain,
        # Reduce chain
        reduce_documents_chain=reduce_documents_chain,
        # The variable name in the llm_chain to put the documents in
        document_variable_name="docs",
        # Return the results of the map steps in the output
        return_intermediate_steps=False,
    )

    files = set([doc.metadata['source'].split('/')[-1] for doc in chunks])

    for file in files:
        file_chunks = [chunk for chunk in chunks if chunk.metadata['source'].split('/')[-1] == file]
        result = map_reduce_chain.invoke(file_chunks)
        file_summary = result["output_text"]
        file_name = file.split('.')[0]
        with open(f"{directory}/{file_name}.txt", "w+") as text_file:
            text_file.write(file_summary)

    print(f"Summaries created on {directory}.")
