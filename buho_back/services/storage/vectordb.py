import os
import chromadb
from chromadb.api.types import QueryResult
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from typing import List, Dict, Optional
from buho_back.config import EMBEDDING_MODEL, OPENAI_API_KEY
from buho_back.services.storage.file_management import get_vectordb_directory


class VectorDbClient:
    def __init__(self, path):
        self.path = path
        self.client = chromadb.PersistentClient(
            path=path, settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY, model_name=EMBEDDING_MODEL
        )
        self.collection_name = "collection"
        self.client.clear_system_cache()

    def get_or_create_collection(self):
        collection = self.client.get_or_create_collection(
            name=self.collection_name, embedding_function=self.embedding_function
        )

        def retrieve_chunks(text, k=3, distance_threshold=None):
            first_k = 10
            query_results = collection.query(
                query_texts=text,
                n_results=first_k,
            )
            formatted_query_results = query_result_to_dict_list(query_results)

            for d in formatted_query_results:
                similarity = jaccard_similarity(text, d.get("document", ""))
                d["jaccard_similarity"] = similarity
                d["semantic_similarity"] = 1 / d["distance"]
                d["hybrid_similarity"] = (
                    d["jaccard_similarity"] * d["semantic_similarity"]
                )

            formatted_query_results.sort(
                key=lambda x: x["hybrid_similarity"], reverse=True
            )
            formatted_query_results = formatted_query_results[:k]

            if distance_threshold:
                filtered_formatted_query_results = [
                    result
                    for result in formatted_query_results
                    if result["distance"] < distance_threshold
                ]
                return filtered_formatted_query_results
            else:
                return formatted_query_results

        collection.retrieve_chunks = retrieve_chunks
        return collection


def get_vectordb(user, deal):
    vectordb_directory = get_vectordb_directory(user, deal)
    if os.path.exists(vectordb_directory):
        try:
            vectordb_client = VectorDbClient(vectordb_directory)
            vectordb = vectordb_client.get_or_create_collection()
        except Exception as e:
            print(f"Couldn't load vectorstore from {vectordb_directory}. Error: {e}")
            vectordb = None
    else:
        vectordb = None
    return vectordb


def query_result_to_dict_list(
    query_result: QueryResult,
) -> List[Dict[str, Optional[str]]]:
    result_list = []

    ids = query_result.get("ids", [])[0]
    metadatas = query_result.get("metadatas", [])[0]
    documents = query_result.get("documents", [])[0]
    distances = query_result.get("distances", [])[0]

    for i in range(len(ids)):
        result_dict = {
            "id": ids[i] if i < len(ids) and ids[i] else None,
            "metadata": (metadatas[i] if i < len(metadatas) and metadatas[i] else None),
            "document": (documents[i] if i < len(documents) and documents[i] else None),
            "distance": (distances[i] if i < len(distances) and distances[i] else None),
        }
        result_list.append(result_dict)
    return result_list


def jaccard_similarity(str1, str2):
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    if not union:
        return 0.0  # Avoid division by zero
    similarity = len(intersection) / len(union)

    return similarity
