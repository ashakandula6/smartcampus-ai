import faiss
import numpy as np
import pickle
import io
import os
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

settings = get_settings()

_embedding_model = None
LOCAL_INDEX_DIR = "local_indexes"
os.makedirs(LOCAL_INDEX_DIR, exist_ok=True)


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        print("[RAG] Loading embedding model (first time — may take 30s)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[RAG] Embedding model loaded!")
    return _embedding_model


def embed_chunks(chunks: List[Dict]) -> np.ndarray:
    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    print(f"[RAG] Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    print(f"[RAG] FAISS index built: {index.ntotal} vectors, dim={dimension}")
    return index


def serialize_index(index: faiss.Index, chunks: List[Dict]) -> bytes:
    buffer = io.BytesIO()
    data = {
        "faiss_bytes": faiss.serialize_index(index).tobytes(),
        "chunks": chunks,
    }
    pickle.dump(data, buffer)
    return buffer.getvalue()


def deserialize_index(data_bytes: bytes) -> Tuple[faiss.Index, List[Dict]]:
    buffer = io.BytesIO(data_bytes)
    data = pickle.load(buffer)
    faiss_array = np.frombuffer(data["faiss_bytes"], dtype=np.uint8)
    index = faiss.deserialize_index(faiss_array)
    return index, data["chunks"]


def save_index_locally(document_id: str, data: bytes) -> str:
    """Save index to local disk as fallback."""
    path = os.path.join(LOCAL_INDEX_DIR, f"{document_id}.pkl")
    with open(path, "wb") as f:
        f.write(data)
    return path


def load_index_locally(document_id: str) -> bytes:
    path = os.path.join(LOCAL_INDEX_DIR, f"{document_id}.pkl")
    with open(path, "rb") as f:
        return f.read()


def build_and_store_index(document_id: str, chunks: List[Dict]) -> str:
    """Build FAISS index from chunks. Try S3 first, fallback to local disk."""
    embeddings = embed_chunks(chunks)
    index = build_faiss_index(embeddings)
    serialized = serialize_index(index, chunks)

    s3_key = f"indexes/{document_id}/faiss.pkl"

    # Try S3
    try:
        from app.services.s3_service import s3_service
        s3_service.upload_bytes(serialized, s3_key)
        print(f"[RAG] Index saved to S3: {s3_key}")
        return s3_key
    except Exception as e:
        print(f"[RAG] S3 save failed, using local disk: {e}")
        local_path = save_index_locally(document_id, serialized)
        print(f"[RAG] Index saved locally: {local_path}")
        return f"local:{document_id}"  # special prefix so we know it's local


def retrieve_relevant_chunks(
    faiss_index_key: str,
    query: str,
    top_k: int = 5,
) -> List[Dict]:
    """Load index (S3 or local) and retrieve top_k relevant chunks for a query."""

    # Load index bytes
    if faiss_index_key.startswith("local:"):
        document_id = faiss_index_key.replace("local:", "")
        data_bytes = load_index_locally(document_id)
        print(f"[RAG] Loaded index from local disk for doc {document_id}")
    else:
        from app.services.s3_service import s3_service
        data_bytes = s3_service.download_bytes(faiss_index_key)
        print(f"[RAG] Loaded index from S3: {faiss_index_key}")

    index, chunks = deserialize_index(data_bytes)

    # Embed query
    model = get_embedding_model()
    query_vec = model.encode([query], show_progress_bar=False).astype("float32")
    faiss.normalize_L2(query_vec)

    # Search
    distances, indices = index.search(query_vec, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1 and idx < len(chunks):
            chunk = chunks[idx].copy()
            chunk["score"] = float(dist)
            results.append(chunk)

    print(f"[RAG] Retrieved {len(results)} chunks for query: '{query[:50]}...'")
    return results