"""
Milestone 4 - Embed chunks into ChromaDB and retrieve by semantic similarity.

    build_index()       embed all chunks (all-MiniLM-L6-v2) into a persistent ChromaDB collection
    retrieve(query, k)  return the top-k most similar chunks with source + distance

Run directly to (re)build the index and test retrieval:  python index.py
"""

import chromadb
from chromadb.utils import embedding_functions

from ingest import load_documents, chunk_documents

CHROMA_DIR = "chroma_db"
COLLECTION = "unofficial_guide"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
_client = chromadb.PersistentClient(path=CHROMA_DIR)


def _collection():
    return _client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embedder,
        metadata={"hnsw:space": "cosine"},   # cosine distance, range ~0..2
    )


def build_index() -> int:
    """(Re)build the vector store from the chunk pipeline. Returns the chunk count."""
    try:
        _client.delete_collection(COLLECTION)   # start clean so re-runs don't duplicate
    except Exception:
        pass
    col = _collection()
    chunks = chunk_documents(load_documents())
    col.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "title": c["title"],
                    "url": c["url"], "chunk_index": c["chunk_index"]} for c in chunks],
    )
    return len(chunks)


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k chunks for a query: {text, source, title, url, distance}."""
    res = _collection().query(query_texts=[query], n_results=k)
    return [
        {"text": t, "source": m["source"], "title": m["title"], "url": m["url"], "distance": d}
        for t, m, d in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks into ChromaDB collection '{COLLECTION}' (cosine, {EMBED_MODEL})\n")

    tests = [
        "Is the NEU meal plan worth the cost?",
        "What should I expect from an OSCCR hearing?",
        "What is Melvin Hall like as a dorm?",
    ]
    for q in tests:
        print(f"QUERY: {q}")
        for i, r in enumerate(retrieve(q), 1):
            print(f"  {i}. dist={r['distance']:.3f}  [{r['source']}]  {r['text'][:110].strip()}...")
        print()
