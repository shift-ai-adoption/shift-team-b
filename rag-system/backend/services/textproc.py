"""Text extraction and chunking utilities."""
import io
import re


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    # txt / md / anything else: treat as utf-8 text
    return data.decode("utf-8", errors="replace")


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Token-approximate chunking.

    Japanese text ≈ 1 token per char; use characters as a proxy
    (chunk_size tokens ≈ chunk_size chars for JA, conservative for EN).
    """
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    step = max(chunk_size - overlap, 1)
    chunks = []
    for start in range(0, len(text), step):
        piece = text[start:start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(text):
            break
    return chunks
