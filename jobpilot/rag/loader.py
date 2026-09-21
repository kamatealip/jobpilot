from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader

def load_resume(file_path):
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return PyPDFLoader(file_path).load()
    elif suffix in {".txt", ".md"}:
        return TextLoader(file_path, encoding="utf-8").load()
    else:
        raise ValueError(f"Unsupported file type: {suffix}")