import re
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    text = text.replace("\u0000", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def derive_title(file_name: str) -> str:
    stem = Path(file_name).stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in stem.split())
