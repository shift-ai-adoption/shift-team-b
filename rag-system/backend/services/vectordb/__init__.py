"""Vector DB registry — all 3 DBs receive documents simultaneously."""
from functools import lru_cache

from .base import VectorDBBase
from .chroma_db import ChromaDB
from .pgvector_db import PgVectorDB
from .qdrant_db import QdrantDB

DB_NAMES = ["pgvector", "chroma", "qdrant"]


@lru_cache(maxsize=None)
def get_db(name: str) -> VectorDBBase:
    if name == "pgvector":
        return PgVectorDB()
    if name == "chroma":
        return ChromaDB()
    if name == "qdrant":
        return QdrantDB()
    raise ValueError(f"unknown vector db: {name}")


def all_dbs() -> list[VectorDBBase]:
    return [get_db(n) for n in DB_NAMES]
