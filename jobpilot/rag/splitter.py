from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_resume(documents):
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    return splitter.split_documents(documents)