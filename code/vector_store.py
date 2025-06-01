import uuid
from chromadb import PersistentClient

chroma_client = PersistentClient(path="chromadb_data")

# ✅ Create or load vector collection
collection = chroma_client.get_or_create_collection("infinite_memory")


def add_to_vector_store(text: str, metadata: dict = None, doc_id: str = None):
    """
    Add a new document to the vector store.
    """
    if metadata is None:
        metadata = {}

    if doc_id is None:
        doc_id = str(uuid.uuid4())

    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )


def retrieve_similar_memories(query: str, k: int = 3):
    """
    Retrieve top-k similar memories based on semantic similarity.
    """
    return collection.query(
        query_texts=[query],
        n_results=k
    )

