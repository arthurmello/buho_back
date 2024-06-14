import os
from langchain.chains import MapReduceDocumentsChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.combine_documents.reduce import ReduceDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import ChatPromptTemplate


def map_chain_setup(llm):
    map_template = """The following is a set of documents
    {docs}
    Based on this list of docs, please summarize them into bullet points.
    Helpful Answer:"""
    map_prompt = ChatPromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)


def reduce_chain_setup(llm):
    reduce_template = """The following is set of summaries:
    {docs}
    Take these and distill it into a final, consolidated summary, using bullet points. 
    Helpful Answer:"""
    reduce_prompt = ChatPromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)


def map_reduce_setup(llm):
    map_chain = map_chain_setup(llm)
    reduce_chain = reduce_chain_setup(llm)

    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_chain, document_variable_name="docs"
    )

    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        collapse_documents_chain=combine_documents_chain,
        token_max=4000,
    )

    map_reduce_chain = MapReduceDocumentsChain(
        llm_chain=map_chain,
        reduce_documents_chain=reduce_documents_chain,
        document_variable_name="docs",
        return_intermediate_steps=False,
    )
    return map_reduce_chain
