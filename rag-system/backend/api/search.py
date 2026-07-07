"""Search API — vector search + LLM answer, per-DB or compare mode."""
import json
import time

from api import role_to_level
from database import (DocumentVersion, OutputTemplate, SearchHistory, get_db,
                      get_setting)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.bedrock import embed_text, generate_answer
from services.vectordb import DB_NAMES, get_db as get_vdb
from sqlalchemy.orm import Session

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    db: str = "pgvector"            # pgvector | chroma | qdrant
    role: str = "general"           # general | manager | executive
    top_k: int | None = None
    template_id: int | None = None
    latest_only: bool = True        # search active versions only
    generate: bool = True           # False = retrieval only (fast test)


def _active_ids(db: Session, latest_only: bool):
    if not latest_only:
        return None
    rows = (db.query(DocumentVersion.id)
            .filter(DocumentVersion.is_active == 1,
                    DocumentVersion.status == "vectorized").all())
    return [r[0] for r in rows]


@router.post("/api/search")
def search(req: SearchRequest, db: Session = Depends(get_db)):
    if req.db not in DB_NAMES:
        raise HTTPException(400, f"db must be one of {DB_NAMES}")
    top_k = req.top_k or int(get_setting(db, "top_k", "5"))
    max_vis = role_to_level(req.role)

    template = None
    if req.template_id:
        template = db.get(OutputTemplate, req.template_id)
        if not template:
            raise HTTPException(404, "template not found")
        if template.min_role_level > max_vis:
            raise HTTPException(403, "この役職ではこのテンプレートを使用できません")

    emb = embed_text(req.query)
    t0 = time.time()
    hits = get_vdb(req.db).search(emb, top_k=top_k, max_visibility=max_vis,
                                  active_docver_ids=_active_ids(db, req.latest_only))
    latency_ms = int((time.time() - t0) * 1000)

    answer, prompt = (None, None)
    if req.generate:
        answer, prompt = generate_answer(
            req.query, hits,
            template.structure if template else None)

    hist = SearchHistory(
        query=req.query, prompt=prompt, answer=answer, db_used=req.db,
        role=req.role, template_id=req.template_id, top_k=top_k,
        hits_json=json.dumps(hits, ensure_ascii=False),
        latency_ms=latency_ms)
    db.add(hist)
    db.commit()

    return {"history_id": hist.id, "query": req.query, "db": req.db,
            "role": req.role, "top_k": top_k, "latency_ms": latency_ms,
            "hits": hits, "answer": answer,
            "template": template.name if template else None}


@router.get("/api/search/compare")
def compare(query: str, role: str = "general", top_k: int = 5,
            latest_only: bool = True, db: Session = Depends(get_db)):
    """Run the same query against all 3 vector DBs and compare results."""
    max_vis = role_to_level(role)
    emb = embed_text(query)
    ids = _active_ids(db, latest_only)
    out = {}
    for name in DB_NAMES:
        t0 = time.time()
        try:
            hits = get_vdb(name).search(emb, top_k=top_k,
                                        max_visibility=max_vis,
                                        active_docver_ids=ids)
            out[name] = {"latency_ms": int((time.time() - t0) * 1000),
                         "hits": hits}
        except Exception as e:
            out[name] = {"error": str(e)}
    hist = SearchHistory(query=query, db_used="compare", role=role,
                         top_k=top_k,
                         hits_json=json.dumps(out, ensure_ascii=False),
                         latency_ms=sum(v.get("latency_ms", 0)
                                        for v in out.values()))
    db.add(hist)
    db.commit()
    return {"history_id": hist.id, "query": query, "results": out}
