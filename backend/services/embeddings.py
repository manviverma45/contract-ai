import re
from collections import Counter


def tokenize(text):
    return re.findall(
        r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
        text.lower()
    )


def create_embedding(text):
    words = tokenize(text)

    if not words:
        return {}

    counts = Counter(words)
    total = len(words)

    return {
        word: count / total
        for word, count in counts.items()
    }


def create_embeddings(texts):
    return [
        create_embedding(text)
        for text in texts
    ]