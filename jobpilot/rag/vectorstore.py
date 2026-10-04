import uuid
from pathlib import Path

from langchain_chroma import Chroma

from jobpilot.rag.embeddings import get_embeddings


def build_vector_store(chunks, persist_directory, collection_name="jobpilot_documents"):
    if not chunks:
        return None

    persist_dir = Path(persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)
    embedding_function = get_embeddings()
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata or {} for chunk in chunks]
    embeddings = embedding_function.embed_documents(texts)
    ids = [str(uuid.uuid4()) for _ in chunks]

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=None,
        persist_directory=str(persist_dir),
        create_collection_if_not_exists=True,
    )

    vector_store._collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return vector_store
