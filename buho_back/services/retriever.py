from chromadb.api.types import QueryResult
from typing import List, Dict, Optional


def query_result_to_dict_list(
    query_result: QueryResult,
) -> List[Dict[str, Optional[str]]]:
    result_list = []

    ids = query_result.get("ids", [])
    metadatas = query_result.get("metadatas", [])
    documents = query_result.get("documents", [])
    distances = query_result.get("distances", [])

    for i in range(len(ids)):
        result_dict = {
            "id": ids[i][0] if i < len(ids) and ids[i] else None,
            "metadata": (
                metadatas[i][0] if i < len(metadatas) and metadatas[i] else None
            ),
            "document": (
                documents[i][0] if i < len(documents) and documents[i] else None
            ),
            "distance": (
                distances[i][0] if i < len(distances) and distances[i] else None
            ),
        }
        result_list.append(result_dict)
    return result_list


def retrieve_chunks(collection, text, k=10, score_threshold=-0.1):

    query_results = collection.query(
        query_texts=text,
        n_results=k,
    )
    formatted_query_results = query_result_to_dict_list(query_results)
    if score_threshold:
        filtered_formatted_query_results = [
            result
            for result in formatted_query_results
            if result["distance"] > score_threshold
        ]
        return filtered_formatted_query_results
    else:
        return formatted_query_results
