from pypdf import PdfReader
from docx import Document
import io

def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()

    if name.endswith('.pdf'):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if name.endswith('.docx'):
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    if name.endswith('.txt'):
        return file_bytes.decode('utf-8', errors='ignore')

    raise ValueError(f"Unsupported file type: {filename}")