"""ChromaDB adapter (HTTP client)."""
import os

import chromadb

from .base import VectorDBBase

COLLECTION = "rag_chunks"


class ChromaDB(VectorDBBase):
    name = "chroma"

    def __init__(self):
        self._client = chromadb.HttpClient(
            host=os.environ.get("CHROMA_HOST", "chromadb"),
            port=int(os.environ.get("CHROMA_PORT", "8000")))
        self._col = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"})

    def upsert(self, chunks):
        if not chunks:
            return
        self._col.upsert(
            ids=[f"{c['document_version_id']}_{c['chunk_index']}" for c in chunks],
            embeddings=[c["embedding"] for c in chunks],
            documents=[c["content"] for c in chunks],
            metadatas=[dict(document_version_id=c["document_version_id"],
                            filename=c["filename"], version=c["version"],
                            visibility_level=c["visibility_level"])
                       for c in chunks])

    def search(self, embedding, top_k=5, max_visibility=3,
               active_docver_ids=None):
        where = {"visibility_level": {"$lte": max_visibility}}
        if active_docver_ids is not None:
            if not active_docver_ids:
                return []
            where = {"$and": [where,
                              {"document_version_id": {"$in": active_docver_ids}}]}
        res = self._col.query(query_embeddings=[embedding], n_results=top_k,
                              where=where)
        out = []
        if res["ids"] and res["ids"][0]:
            for doc, meta, dist in zip(res["documents"][0],
                                       res["metadatas"][0],
                                       res["distances"][0]):
                out.append(dict(content=doc, score=1.0 - float(dist),
                                filename=meta["filename"],
                                version=meta["version"],
                                document_version_id=meta["document_version_id"]))
        return out

    def delete_by_docver(self, document_version_id: int) -> None:
        self._col.delete(where={"document_version_id": document_version_id})
