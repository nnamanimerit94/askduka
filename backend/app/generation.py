"""
Generation contract — owned by Member 4.

The webhook orchestrator imports generate_answer from here. This
stub keeps the contract importable and the end-to-end flow testable
while the real Claude implementation is built.

Contract:
    generate_answer(customer_message, chunks) -> {
        "answer": str,
        "sources": list[str],
        "confidence": "grounded" | "fallback",
    }

Note on the signature: the project plan originally specified
generate_answer(customer_message, business_id). Retrieval is
performed by the orchestrator and passed in instead, so generation
stays pure prompt construction + Claude call and never touches the
database.

TODO(Member 4): replace the grounded branch below with the Claude
API call (ANTHROPIC_API_KEY), using the retrieved chunks as context.
The fallback branch is final and can stay as-is.
"""

FALLBACK_ANSWER = (
    "Sorry, I don't have an answer to that yet. "
    "Please message the owner directly."
)


def generate_answer(
    customer_message: str,
    chunks: list[dict],
) -> dict:
    """
    Answer a customer message from retrieved document chunks.

    No relevant chunks were found → fallback response, so the
    customer never receives an invented answer.
    """
    if not chunks:
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": "fallback",
        }

    # TODO(Member 4): Claude API call grounded in `chunks`.
    # Placeholder: echo the best-matching chunk so the flow is
    # demoable end-to-end before the real prompt exists.
    top_chunk = chunks[0]

    return {
        "answer": top_chunk["chunk_text"],
        "sources": [top_chunk["source_document"]],
        "confidence": "grounded",
    }
