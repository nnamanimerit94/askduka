from backend.app.ingestion.chunker import chunk_text


def test_chunk_text():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    chunks = chunk_text(
        text,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert len(chunks) > 1
    assert chunks[0] == "ABCDEFGHIJ"
    assert chunks[1].startswith("IJ")


def test_empty_text():
    assert chunk_text("") == []


def test_invalid_chunk_size():
    try:
        chunk_text("hello", chunk_size=0)
        assert False
    except ValueError:
        assert True


def test_invalid_overlap():
    try:
        chunk_text("hello", chunk_size=10, chunk_overlap=10)
        assert False
    except ValueError:
        assert True
