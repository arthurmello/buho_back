def retrieve_chunks(vector_store, text, k=10):
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": -0.1},
    )
    chunks = retriever.invoke(text)
    return chunks
