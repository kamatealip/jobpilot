from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

def load_resume(file_path):
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return PyPDFLoader(file_path).load()
    elif suffix in {".txt", ".md", ".csv"}:
        return TextLoader(file_path, encoding="utf-8").load()
    elif suffix == ".docx":
        return [_load_docx(file_path)]
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def documents_to_text(documents) -> str:
    return "\n\n".join(document.page_content for document in documents if document.page_content)


def _load_docx(file_path: str) -> Document:
    with ZipFile(file_path) as archive:
        xml_bytes = archive.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(
            node.text or ""
            for node in paragraph.findall(".//w:t", namespace)
        ).strip()
        if text:
            paragraphs.append(text)

    return Document(
        page_content="\n".join(paragraphs),
        metadata={"source": file_path},
    )
