from pathlib import Path

from langchain_chroma import Chroma

from jobpilot.rag.embeddings import get_embeddings


def build_vector_store(chunks, persist_directory, collection_name="jobpilot_documents"):
    if not chunks:
        return None

    persist_dir = Path(persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(persist_dir),
        collection_name=collection_name,
    )

    return vector_store