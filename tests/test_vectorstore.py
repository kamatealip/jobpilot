import unittest
from unittest.mock import ANY, MagicMock, patch

from langchain_core.documents import Document

from jobpilot.rag.vectorstore import build_vector_store


class BuildVectorStoreTests(unittest.TestCase):
    @patch("jobpilot.rag.vectorstore.Chroma")
    @patch("jobpilot.rag.vectorstore.get_embeddings")
    def test_build_vector_store_precomputes_embeddings_before_upsert(
        self, mock_get_embeddings, mock_chroma
    ):
        mock_embedding_fn = MagicMock()
        mock_embedding_fn.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_get_embeddings.return_value = mock_embedding_fn

        mock_vector_store = MagicMock()
        mock_chroma.return_value = mock_vector_store

        documents = [
            Document(page_content="first chunk", metadata={"source": "a"}),
            Document(page_content="second chunk", metadata={"source": "b"}),
        ]

        build_vector_store(documents, "/tmp/jobpilot_vectorstore", "demo_collection")

        mock_embedding_fn.embed_documents.assert_called_once_with(
            ["first chunk", "second chunk"]
        )

        mock_chroma.assert_called_once_with(
            collection_name="demo_collection",
            embedding_function=None,
            persist_directory="/tmp/jobpilot_vectorstore",
            create_collection_if_not_exists=True,
        )

        mock_vector_store._collection.upsert.assert_called_once()
        _, kwargs = mock_vector_store._collection.upsert.call_args
        self.assertEqual(kwargs["documents"], ["first chunk", "second chunk"])
        self.assertEqual(kwargs["metadatas"], [{"source": "a"}, {"source": "b"}])
        self.assertEqual(kwargs["embeddings"], [[0.1, 0.2], [0.3, 0.4]])
        self.assertEqual(len(kwargs["ids"]), 2)
        self.assertTrue(all(isinstance(id_value, str) for id_value in kwargs["ids"]))


if __name__ == "__main__":
    unittest.main()
