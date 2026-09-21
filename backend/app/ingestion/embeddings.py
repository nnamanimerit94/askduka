from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for document chunks.

    Document embeddings are stored in the database and later
    compared with query embeddings during retrieval.
    """
    if not texts:
        return []

    model = get_model()

    embeddings = model.encode_document(
        texts,
        convert_to_numpy=True,
    )

    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for a user's search query.
    """
    if not text or not text.strip():
        raise ValueError("Query text cannot be empty.")

    model = get_model()

    embedding = model.encode_query(
        text,
        convert_to_numpy=True,
    )

    embedding = embedding.tolist()

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Query embedding must contain exactly "
            f"{EMBEDDING_DIMENSION} dimensions."
        )

    return embedding
