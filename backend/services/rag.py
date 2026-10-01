import math
import re
from collections import Counter

from services.embeddings import create_embedding


def tokenize(text):
    return re.findall(
        r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
        text.lower()
    )


def build_index(chunks):
    if not chunks:
        return None

    documents = []

    for chunk in chunks:
        words = tokenize(chunk["text"])
        counts = Counter(words)

        documents.append({
            "tf": counts,
            "length": len(words)
        })

    document_frequency = Counter()

    for document in documents:
        for word in document["tf"]:
            document_frequency[word] += 1

    total_documents = len(documents)

    idf = {}

    for word, frequency in document_frequency.items():
        idf[word] = math.log(
            (total_documents + 1)
            / (frequency + 1)
        ) + 1

    vectors = []

    for document in documents:
        vector = {}

        for word, count in document["tf"].items():
            vector[word] = (
                (1 + math.log(count))
                * idf.get(word, 1)
            )

        vectors.append(vector)

    return {
        "vectors": vectors,
        "idf": idf
    }


def cosine_similarity(vector_a, vector_b):
    if not vector_a or not vector_b:
        return 0.0

    common_words = set(vector_a) & set(vector_b)

    if not common_words:
        return 0.0

    dot = sum(
        vector_a[word] * vector_b[word]
        for word in common_words
    )

    norm_a = math.sqrt(
        sum(value * value for value in vector_a.values())
    )

    norm_b = math.sqrt(
        sum(value * value for value in vector_b.values())
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def search_index(index, chunks, query, top_k=6):
    if not index or not chunks or not query:
        return []

    query_words = tokenize(query)

    if not query_words:
        return []

    query_counts = Counter(query_words)
    query_vector = {}

    for word, count in query_counts.items():
        query_vector[word] = (
            (1 + math.log(count))
            * index["idf"].get(word, 1)
        )

    results = []

    for position, chunk in enumerate(chunks):
        if position >= len(index["vectors"]):
            continue

        score = cosine_similarity(
            query_vector,
            index["vectors"][position]
        )

        # Small bonus when the complete query appears in the chunk.
        query_text = " ".join(query_words)
        chunk_text = " ".join(tokenize(chunk["text"]))

        if query_text and query_text in chunk_text:
            score += 0.15

        if score > 0:
            results.append({
                "text": chunk["text"],
                "source": chunk.get("source", {}),
                "chunk_index": chunk.get("chunk_index", 0),
                "score": float(score)
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]