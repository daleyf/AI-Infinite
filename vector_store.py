"""
vector_store.py

A simple wrapper around Chroma to store and retrieve "memory chunks" via embeddings.
"""

import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from config import CHROMA_PERSIST_DIR, OPENAI_API_KEY

# ------------------------------------------------------------------------------
# 1) Initialize Chroma client and embedding function
# ------------------------------------------------------------------------------
# Make sure the persist directory exists:
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Use the OpenAI embedding function
# (We rely on OpenAI’s text-embedding-ada-002 under the hood)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"  # Extra: you can pick a different embedding model if desired
)

client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_PERSIST_DIR,
        anonymized_telemetry=False
    )
)

# Create (or get) a collection for memory chunks:
collection = client.get_or_create_collection(
    name="memory_chunks",
    embedding_function=openai_ef
)


def add_memory_chunk(chunk_id: str, text: str) -> None:
    """
    add_memory_chunk(chunk_id, text) -> None

    - chunk_id: unique string ID for this memory chunk
    - text: the text to embed and store
    
    This function adds the embedding + text to Chroma under `chunk_id`.
    """
    # Chroma expects: (ids: List[str], texts: List[str])
    collection.add(
        ids=[chunk_id],
        documents=[text]
        # embeddings are generated automatically by the embedding function
    )


def query_similar_memory(query_text: str, top_k: int = 5) -> list[dict]:
    """
    query_similar_memory(query_text, top_k) -> List[{"id":..., "document":..., "distance":...}, ...]

    Returns the top_k most similar memory chunks for `query_text`.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    # results["ids"][0] is a list of top_k IDs, results["documents"][0] is their texts
    ids = results["ids"][0]
    docs = results["documents"][0]
    distances = results["distances"][0]
    return [
        {"id": _id, "document": _doc, "distance": _dist}
        for _id, _doc, _dist in zip(ids, docs, distances)
    ]


def persist_vector_store() -> None:
    """
    persist_vector_store() -> None

    Flush Chroma’s data to disk. Call this before shutting down if you want to keep the memory.
    """
    client.persist()
