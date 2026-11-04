from backend.app.catalog_answers import answer_from_catalog


def test_clear_product_question_returns_saved_catalog_line():
    result = answer_from_catalog(
        "How much is the 20 inch wig?",
        ["20 inch wig: NGN 120000", "Lagos delivery: 2 days"],
    )
    assert result["answer"] == "20 inch wig: NGN 120000"


def test_unknown_product_does_not_invent_an_answer():
    result = answer_from_catalog("How much is the refrigerator?", ["Wig: NGN 50000"])
    assert result["answer"] is None


def test_ambiguous_catalog_does_not_guess():
    result = answer_from_catalog(
        "How much is the wig?",
        ["Wig A: NGN 50000", "Wig B: NGN 70000"],
    )
    assert result["answer"] is None


def test_empty_question_does_not_match():
    assert answer_from_catalog("???", ["20 inch wig: NGN 120000"])["answer"] is None
