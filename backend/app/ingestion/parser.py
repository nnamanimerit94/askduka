from pathlib import Path

from pypdf import PdfReader


SUPPORTED_FILE_TYPES = {".txt", ".pdf"}


def extract_text(file_path: str) -> str:
    """
    Extract text from a supported document.

    Supported formats:
    - .txt
    - .pdf
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_type = path.suffix.lower()

    if file_type not in SUPPORTED_FILE_TYPES:
        raise ValueError(
            f"Unsupported file type: {file_type}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_FILE_TYPES))}"
        )

    if file_type == ".txt":
        return path.read_text(encoding="utf-8").strip()

    if file_type == ".pdf":
        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text.strip())

        return "\n\n".join(pages).strip()

    raise ValueError(f"Unsupported file type: {file_type}")