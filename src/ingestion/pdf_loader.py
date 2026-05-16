from pypdf import PdfReader


def extract_text(file_bytes: bytes) -> str:
    import io

    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text
