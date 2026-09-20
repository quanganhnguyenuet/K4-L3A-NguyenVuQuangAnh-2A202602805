from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._chroma_client = None
        self._next_index = 0

        try:
            import chromadb

            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
            self._chroma_client = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build one normalized in-memory record from a Document."""
        metadata = dict(doc.metadata)
        # A chunk normally has an id such as ``original-document#2`` while
        # its metadata must retain ``original-document``.  Keep a caller's
        # explicit parent id and only provide a sensible default for ordinary
        # unchunked documents.
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}-{self._next_index}",
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": metadata,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run dot-product similarity search over an already filtered record set."""
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
            return

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            collection_size = self._collection.count()
            if collection_size == 0:
                return []
            response = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=min(top_k, collection_size),
                include=["documents", "metadatas", "distances"],
            )
            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]
            return [
                {
                    "id": record_id,
                    "content": content,
                    "metadata": metadata or {},
                    # The collection uses cosine distance, so higher is better
                    # after converting it back to cosine similarity.
                    "score": 1.0 - distance,
                }
                for record_id, content, metadata, distance in zip(ids, documents, metadatas, distances)
            ]

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            collection_size = self._collection.count()
            if collection_size == 0:
                return []
            response = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=min(top_k, collection_size),
                where=metadata_filter,
                include=["documents", "metadatas", "distances"],
            )
            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]
            return [
                {
                    "id": record_id,
                    "content": content,
                    "metadata": metadata or {},
                    "score": 1.0 - distance,
                }
                for record_id, content, metadata, distance in zip(ids, documents, metadatas, distances)
            ]

        filtered_records = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            matching = self._collection.get(where={"doc_id": doc_id})
            ids = matching.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        size_before = len(self._store)
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < size_before
