"""Common interface for vector DB adapters."""
from abc import ABC, abstractmethod


class VectorDBBase(ABC):
    name: str = "base"

    @abstractmethod
    def upsert(self, chunks: list[dict]) -> None:
        """chunks: [{id, content, embedding, filename, version,
        document_version_id, chunk_index, visibility_level}]"""

    @abstractmethod
    def search(self, embedding: list[float], top_k: int = 5,
               max_visibility: int = 3,
               active_docver_ids: list[int] | None = None) -> list[dict]:
        """Return [{content, score, filename, version, document_version_id}]"""

    @abstractmethod
    def delete_by_docver(self, document_version_id: int) -> None:
        """Remove all chunks belonging to a document version."""
