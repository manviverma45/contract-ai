import faiss
import numpy as np

from services.embeddings import create_embeddings, create_embedding


def build_index(chunks):
    if not chunks:
        return None

    texts = [chunk["text"] for chunk in chunks]
    embeddings = np.array(
        create_embeddings(texts),
        dtype="float32"
    )

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def search_index(index, chunks, query, top_k=6):
    if index is None or not chunks:
        return []

    query_embedding = np.array(
        [create_embedding(query)],
        dtype="float32"
    )

    limit = min(top_k, len(chunks))

    scores, indices = index.search(
        query_embedding,
        limit
    )

    results = []

    for score, index_position in zip(scores[0], indices[0]):
        if index_position < 0:
            continue

        chunk = chunks[index_position]

        results.append({
            "text": chunk["text"],
            "source": chunk.get("source", {}),
            "chunk_index": chunk.get("chunk_index", 0),
            "score": float(score)
        })

    return results