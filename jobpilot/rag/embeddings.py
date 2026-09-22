import os

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
def get_embeddings():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Add it to your environment before creating embeddings."
        )

    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2"
    )
