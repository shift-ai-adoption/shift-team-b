"""pgvector adapter (PostgreSQL)."""
from sqlalchemy import text

from database import engine

from .base import VectorDBBase


def _vec(embedding: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"


class PgVectorDB(VectorDBBase):
    name = "pgvector"

    def upsert(self, chunks: list[dict]) -> None:
        with engine.begin() as conn:
            for c in chunks:
                conn.execute(text(
                    "INSERT INTO chunks (document_version_id, chunk_index, "
                    "content, embedding, visibility_level, filename, version) "
                    "VALUES (:dv, :ci, :co, :emb, :vis, :fn, :ver)"),
                    dict(dv=c["document_version_id"], ci=c["chunk_index"],
                         co=c["content"], emb=_vec(c["embedding"]),
                         vis=c["visibility_level"], fn=c["filename"],
                         ver=c["version"]))

    def search(self, embedding, top_k=5, max_visibility=3,
               active_docver_ids=None):
        where = "visibility_level <= :vis"
        params = {"emb": _vec(embedding), "vis": max_visibility, "k": top_k}
        if active_docver_ids is not None:
            if not active_docver_ids:
                return []
            where += " AND document_version_id = ANY(:ids)"
            params["ids"] = active_docver_ids
        sql = text(
            f"SELECT content, filename, version, document_version_id, "
            f"1 - (embedding <=> :emb) AS score "
            f"FROM chunks WHERE {where} "
            f"ORDER BY embedding <=> :emb LIMIT :k")
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
        return [dict(content=r["content"], score=float(r["score"]),
                     filename=r["filename"], version=r["version"],
                     document_version_id=r["document_version_id"])
                for r in rows]

    def delete_by_docver(self, document_version_id: int) -> None:
        with engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM chunks WHERE document_version_id = :dv"),
                {"dv": document_version_id})
