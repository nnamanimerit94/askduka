"""Deterministic catalog lookup for the first customer Q&A vertical slice.

No LLM, embeddings, or external provider is required. Only return an
explicit catalog line when the customer question clearly matches it.
"""
import re

STOP_WORDS = frozenset({
    "a", "an", "and", "are", "can", "cost", "do", "does", "for",
    "how", "i", "is", "me", "much", "of", "please", "price",
    "the", "to", "what", "you", "your", "have", "in", "on",
})


def tokens(text: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 1 and word not in STOP_WORDS
    }


def answer_from_catalog(question: str, lines: list[str]) -> dict:
    """Return a catalog fact only for an unambiguous match."""
    query_terms = tokens(question)
    if not query_terms:
        return {"answer": None, "matched_lines": []}

    scored = []
    for line in lines:
        if not isinstance(line, str) or not line.strip():
            continue
        line_terms = tokens(line)
        overlap = query_terms & line_terms
        if not overlap:
            continue
        coverage = len(overlap) / len(query_terms)
        if coverage >= 0.75:
            scored.append((coverage, line.strip()))

    if not scored:
        return {"answer": None, "matched_lines": []}

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score = scored[0][0]
    best = [line for score, line in scored if score == best_score]
    # Multiple equally matching catalog entries are ambiguous.
    if len(best) != 1:
        return {"answer": None, "matched_lines": []}
    return {"answer": best[0], "matched_lines": best}
