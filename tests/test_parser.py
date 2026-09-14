from backend.app.ingestion.parser import extract_text


def test_extract_text():
    text = extract_text("tests/fixtures/sample_catalog.txt")

    assert "AskDuka Sample Business" in text
    assert "Jollof Rice" in text
    assert "₦2,500" in text
    assert "Port Harcourt" in text


def test_unsupported_file_type(tmp_path):
    file_path = tmp_path / "sample.docx"
    file_path.write_text("test")

    try:
        extract_text(str(file_path))
        assert False
    except ValueError as error:
        assert "Unsupported file type" in str(error)

def test_extract_pdf_text():
    text = extract_text(
        "tests/fixtures/askduka_sample_catalog.pdf"
    )

    assert "AskDuka Sample Business" in text
    assert "Jollof Rice" in text
    assert "Fried Rice" in text
    assert "Port Harcourt" in text
    assert "Opening Hours" in text