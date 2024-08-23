import os
import concurrent.futures
import uuid
import tiktoken

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from buho_back.services.storage.vectordb import VectorDbClient
from buho_back.services.storage.file_management import (
    clear_path,
    dump_json,
    get_summaries_directory,
    get_dashboard_data_directory,
    get_vectordb_directory,
)
from buho_back.utils import ChatModel, extract_dict, extract_url
from buho_back.config import EMBEDDING_MODEL, CHUNKING_PARAMS

from buho_back.services.answer import create_general_context

chat_model = ChatModel()

extension_loaders = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader,
}


def calculate_embedding_cost(texts):
    enc = tiktoken.encoding_for_model(EMBEDDING_MODEL)
    total_tokens = sum([len(enc.encode(page)) for page in texts])
    # check prices here: https://openai.com/pricing
    return total_tokens, total_tokens / 1000 * 0.00013


def load_file(file):
    name, extension = os.path.splitext(file)
    try:
        loader = extension_loaders[extension](file)
    except:
        print("Document format is not supported!")
        return None

    print(f'Loading "{file}"')
    data = loader.load()
    for doc in data:
        doc.page_content = doc.page_content.replace("\n", " ")
    return data


# splitting data in chunks
def create_chunks(data, params=CHUNKING_PARAMS):
    chunk_size = params["chunk_size"]
    chunk_overlap = params["chunk_overlap"]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(data)
    return chunks


# create embeddings and save them in a vector store
def create_vectordb(chunks, user, deal):
    vectordb_directory = get_vectordb_directory(user, deal)
    summaries_directory = get_summaries_directory(user, deal)

    # reset database
    clear_path(vectordb_directory)
    clear_path(summaries_directory)

    vectordb_client = VectorDbClient(vectordb_directory)
    vectordb = vectordb_client.get_or_create_collection()
    documents = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [f"{uuid.uuid4()}" for _ in range(len(chunks))]
    vectordb.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Embeddings created on {vectordb_directory}.")
    return vectordb


def get_unique_files_from_chunks(chunks):
    return set([doc.metadata["source"].split("/")[-1] for doc in chunks])


def get_chunk_content_for_file(chunks, file):
    chunks = [
        chunk.page_content
        for chunk in chunks
        if chunk.metadata["source"].split("/")[-1] == file
    ]
    return chunks


def aggregate_chunks(chunks, max_size):
    aggregated_chunks = []
    current_chunk = ""

    for chunk in chunks:
        if len(current_chunk) + len(chunk) <= max_size:
            current_chunk = "\n".join([current_chunk, chunk])
        else:
            aggregated_chunks.append(current_chunk)
            current_chunk = chunk

    if current_chunk:  # Add the last chunk if it exists
        aggregated_chunks.append(current_chunk)

    return aggregated_chunks


@retry(
    wait=wait_random_exponential(min=15, max=65),
    stop=stop_after_attempt(5),
    reraise=True,
)
def summarize(text):
    prompt = f"""summarize this in bullet points: {text}, cleaning all unnecessary stuff,
        while keeping the maximum amount of relevant information possible"""
    answer = chat_model.invoke(prompt)
    return answer


def summarize_and_aggregate_chunks(chunks, max_size=400000):
    aggregated_chunks = aggregate_chunks(chunks, max_size=max_size)
    api_limit_tokens_per_minute = 30000
    number_of_chunks = len(aggregated_chunks)
    max_workers = int(number_of_chunks * max_size / api_limit_tokens_per_minute)
    available_cpus = os.cpu_count()
    print(f"{number_of_chunks=}")
    print(f"{max_workers=}")
    print(f"{available_cpus=}")
    if len(aggregated_chunks) == 1:
        aggregated_chunks[0] = summarize(aggregated_chunks[0])
    else:
        while len(aggregated_chunks) > 1 or (len(aggregated_chunks[0]) > max_size):
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                summarized_chunks = list(executor.map(summarize, aggregated_chunks))
            aggregated_chunks = aggregate_chunks(summarized_chunks, max_size=max_size)
    return aggregated_chunks[0]


def create_summaries(chunks, user, deal):
    summaries_directory = get_summaries_directory(user, deal)
    print("Creating summaries...")
    clear_path(summaries_directory)
    if not os.path.exists(summaries_directory):
        os.makedirs(summaries_directory)

    files = get_unique_files_from_chunks(chunks)

    for file in files:
        filename = file.split(".")[0]
        print(f"... for file {filename}")
        file_chunks = get_chunk_content_for_file(chunks, file)
        file_summary = summarize_and_aggregate_chunks(file_chunks)
        with open(f"{summaries_directory}/{filename}.txt", "w+") as text_file:
            text_file.write(file_summary)

    print(f"Summaries created on {summaries_directory}.")


class GeneralInfo:
    def __init__(self, user, deal):
        self.user = user
        self.deal = deal
        self.summaries_directory = get_summaries_directory(user, deal)
        self.general_context = create_general_context(self.summaries_directory)

    def get_company_name(self):
        prompt = f"Extract the company name from this summary. no text besides the company name. {self.general_context}"
        return chat_model.invoke(prompt)

    def get_summary(self):
        company_name = self.get_company_name()
        prompt = f"""Given a general context, write a one-paragraph summary for a company called {company_name}. Here's an example for Apple:
            'Apple Inc. is a leading technology company that designs, manufactures, and markets consumer electronics,
            software, and services. Its primary products include the iPhone, iPad, Mac computers, Apple Watch, and
            Apple TV, all of which are powered by its proprietary iOS and macOS operating systems.
            Apple's main sources of revenue are hardware sales, primarily from iPhones, complemented by services
            revenue from the App Store, Apple Music, iCloud, and AppleCare. The company operates globally, with
            significant market presence in North America, Europe, Greater China, and the Asia Pacific region.
            Apple's innovative product ecosystem and strong brand loyalty drive its competitive edge and robust
            financial performance.'
            Here's some context on {company_name}:
            {self.general_context}

            Make sure your summary is concise and straight to the point.
        """
        return chat_model.invoke(prompt)

    def get_logo_url(self):
        company_name = self.get_company_name()
        prompt = f"""give me a url for a company called {company_name} logo.
            no text, just the URL like in this example:
            https://upload.wikimedia.org/wikipedia/fr/9/91/Dataiku_logo.png
        """
        answer = chat_model.invoke(prompt)
        return extract_url(answer)

    def get_kpi(self):
        prompt = f"""Extract the 4 (max) main financial indicators from this, in a structured format:
            {self.general_context}
            Here's an example of the expected format:
            {{"operating_income": "350Mi USD", "gross_revenue": "700Mi USD", "net_working_capital": 1Bi USD"}}

            just answer in this dict-like format, no extra text.
            start your answer with "{{" and finish it with "}}", no extra formatting. avoid special characters, such as line breaks.
        """
        answer = chat_model.invoke(prompt)
        return extract_dict(answer)

    def get_risks(self):
        prompt = f"""List 3 main commercial risks, and 3 main technical risks from this deal
            in a structured format:
            {self.general_context}
            Here's an example of the expected format:
            {{
                "technical": [
                    "Data Center Dependence: Expanding and maintaining data centers is critical, with risks related to land, energy, and component availability.",
                    "Supply Chain Disruptions: Limited suppliers for key components could hinder product manufacturing and delivery.",
                    "Cybersecurity Threats: Ongoing risks from cyberattacks and data breaches could damage reputation and lead to financial losses."
                ],
                "commercial": [
                    "Economic Vulnerability: Microsoft's performance is tied to global economic conditions, impacting demand for its products and services.",
                    "Competitive Pressure: Intense competition from tech giants like Google, Amazon, and Apple in various segments could erode market share.",
                    "Foreign Exchange Risk: Revenue and expenses from international operations are sensitive to currency fluctuations, which could impact profitability."
                ]
            }}

            just answer in this dict-like format, no extra text.
            make it very short and concise.
            start your answer with "{{" and finish it with "}}", no extra formatting. avoid special characters, such as line breaks.
        """
        answer = chat_model.invoke(prompt)
        return extract_dict(answer)

    def get_dashboard_data(self):
        prompt = ""

    def save_dashboard_data(self):
        def get_company_name():
            return self.get_company_name()

        def get_logo_url():
            return self.get_logo_url()

        def get_summary():
            return self.get_summary()

        def get_kpi():
            return self.get_kpi()

        def get_risks():
            return self.get_risks()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_company_name): "company_name",
                executor.submit(get_logo_url): "company_logo",
                executor.submit(get_summary): "deal_summary",
                executor.submit(get_kpi): "kpi",
                executor.submit(get_risks): "risks",
            }

            dashboard_data = {}
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    dashboard_data[key] = result
                except Exception as exc:
                    print(f"{key} generated an exception: {exc}")

        dashboard_data_directory = get_dashboard_data_directory(self.user, self.deal)
        dump_json(dashboard_data, dashboard_data_directory)
        return dashboard_data
