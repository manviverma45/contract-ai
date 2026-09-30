from sentence_transformers import SentenceTransformer


_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model


def create_embeddings(texts):
    if not texts:
        return []

    model = get_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    return embeddings.tolist()


def create_embedding(text):
    if not text:
        return []

    model = get_model()

    embedding = model.encode(
        [text],
        normalize_embeddings=True
    )

    return embedding[0].tolist()