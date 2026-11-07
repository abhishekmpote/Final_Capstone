"""Text extraction for supported healthcare document formats."""

from io import BytesIO
from pathlib import Path


def extract_pages(filename: str, content: bytes) -> list[tuple[int, str]]:
    """Extract normalized text by page; plain text and DOCX use page 1."""
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return [(index, page.extract_text() or "") for index, page in enumerate(reader.pages, 1)]
    if extension == ".docx":
        from docx import Document

        document = Document(BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return [(1, text)]
    if extension == ".txt":
        for encoding in ("utf-8-sig", "utf-8", "cp1252"):
            try:
                return [(1, content.decode(encoding))]
            except UnicodeDecodeError:
                continue
        raise ValueError("The text document could not be decoded.")
    raise ValueError(f"Unsupported document type: {extension}")
