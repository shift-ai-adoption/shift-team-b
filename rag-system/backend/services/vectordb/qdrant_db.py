"""Qdrant adapter."""
import os

from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, FieldCondition, Filter, MatchAny,
                                  PointStruct, Range, VectorParams)

from .base import VectorDBBase

COLLECTION = "rag_chunks"
DIM = 1024


class QdrantDB(VectorDBBase):
    name = "qdrant"

    def __init__(self):
        self._client = QdrantClient(
            host=os.environ.get("QDRANT_HOST", "qdrant"),
            port=int(os.environ.get("QDRANT_PORT", "6333")))
        if not self._client.collection_exists(COLLECTION):
            self._client.create_collection(
                COLLECTION,
                vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))

    def upsert(self, chunks):
        if not chunks:
            return
        points = [
            PointStruct(
                id=c["document_version_id"] * 100000 + c["chunk_index"],
                vector=c["embedding"],
                payload=dict(content=c["content"], filename=c["filename"],
                             version=c["version"],
                             document_version_id=c["document_version_id"],
                             visibility_level=c["visibility_level"]))
            for c in chunks]
        self._client.upsert(COLLECTION, points=points)

    def search(self, embedding, top_k=5, max_visibility=3,
               active_docver_ids=None):
        must = [FieldCondition(key="visibility_level",
                               range=Range(lte=max_visibility))]
        if active_docver_ids is not None:
            if not active_docver_ids:
                return []
            must.append(FieldCondition(key="document_version_id",
                                       match=MatchAny(any=active_docver_ids)))
        res = self._client.query_points(
            COLLECTION, query=embedding, limit=top_k,
            query_filter=Filter(must=must), with_payload=True)
        return [dict(content=p.payload["content"], score=float(p.score),
                     filename=p.payload["filename"],
                     version=p.payload["version"],
                     document_version_id=p.payload["document_version_id"])
                for p in res.points]

    def delete_by_docver(self, document_version_id: int) -> None:
        self._client.delete(
            COLLECTION,
            points_selector=Filter(must=[FieldCondition(
                key="document_version_id",
                match=MatchAny(any=[document_version_id]))]))
