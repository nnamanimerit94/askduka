"""Convert retrieved database chunks into safe generation evidence.

Retrieval returns ORM DocumentChunk objects. Generation accepts plain dicts.
Keep this boundary small and testable without database or AI dependencies.
"""


def prepare_generation_context(results: list[dict], limit: int = 5) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be positive")

    evidence = []
    for result in results:
        if not isinstance(result, dict):
            continue
        chunk = result.get("chunk")
        text = getattr(chunk, "chunk_text", None)
        if not isinstance(text, str) or not text.strip():
            continue
        similarity = result.get("similarity")
        if similarity is not None and (
            not isinstance(similarity, (int, float))
            or not 0 <= similarity <= 1
        ):
            continue
        evidence.append({
            "chunk_text": text.strip(),
            "source_document": str(getattr(chunk, "document_id", "business catalog")),
        })
        if len(evidence) >= limit:
            break
    return evidence
