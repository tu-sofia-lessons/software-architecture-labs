"""The University Assistant: orchestrates the RAG pipeline."""
from pathlib import Path

import llm_client
from rag.chunker import chunk_documents
from rag.loader import load_documents
from rag.prompt import build_prompt
from rag.retriever import retrieve

KNOWLEDGE = Path(__file__).parent.parent / "knowledge"
REFUSAL = "The university documents do not contain this information. Please ask the Student Office."


def ask(question, mode="rag", knowledge_dir=KNOWLEDGE, llm=None):
    """Answer a question. Returns (answer, sources)."""
    llm = llm or llm_client.generate
    if mode == "llm":                                   # LLM only: no system-owned knowledge
        return llm(question), []

    chunks = chunk_documents(load_documents(knowledge_dir))
    # WEEK 09 BUILD: retrieve → decide what to do when nothing relevant is found
    #                → build_prompt → llm → return (answer, sorted list of sources used)
    raise NotImplementedError("Week 09 Build: implement the RAG path in ask()")
