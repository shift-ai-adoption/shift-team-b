"""Evaluation API — quantitative comparison of the 3 vector DBs.

Metrics per DB: Hit Rate @1/@3/@5, Reciprocal Rank, latency.
The expected (ground-truth) document filename is supplied by the user.
"""
import json
import time

from api import role_to_level
from database import DocumentVersion, Evaluation, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.bedrock import embed_text
from services.vectordb import DB_NAMES, get_db as get_vdb
from sqlalchemy.orm import Session

router = APIRouter()


class EvalRequest(BaseModel):
    query: str
    expected_filename: str
    role: str = "executive"     # evaluate over everything by default
    top_k: int = 5
    latest_only: bool = True


@router.post("/api/evaluation")
def run_evaluation(req: EvalRequest, db: Session = Depends(get_db)):
    emb = embed_text(req.query)
    max_vis = role_to_level(req.role)
    ids = None
    if req.latest_only:
        rows = (db.query(DocumentVersion.id)
                .filter(DocumentVersion.is_active == 1,
                        DocumentVersion.status == "vectorized").all())
        ids = [r[0] for r in rows]

    results = {}
    for name in DB_NAMES:
        t0 = time.time()
        try:
            hits = get_vdb(name).search(emb, top_k=req.top_k,
                                        max_visibility=max_vis,
                                        active_docver_ids=ids)
            latency = int((time.time() - t0) * 1000)
            rank = next((i + 1 for i, h in enumerate(hits)
                         if h["filename"] == req.expected_filename), None)
            results[name] = {
                "latency_ms": latency,
                "rank_of_expected": rank,
                "hit@1": bool(rank and rank <= 1),
                "hit@3": bool(rank and rank <= 3),
                "hit@5": bool(rank and rank <= 5),
                "reciprocal_rank": (1.0 / rank) if rank else 0.0,
                "top_hits": [{"filename": h["filename"],
                              "score": round(h["score"], 4)} for h in hits],
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    ev = Evaluation(query=req.query, expected_filename=req.expected_filename,
                    results_json=json.dumps(results, ensure_ascii=False))
    db.add(ev)
    db.commit()
    return {"evaluation_id": ev.id, "query": req.query,
            "expected_filename": req.expected_filename, "results": results}


@router.get("/api/evaluation")
def list_evaluations(db: Session = Depends(get_db)):
    evs = db.query(Evaluation).order_by(Evaluation.id.desc()).limit(100).all()
    return [{"id": e.id, "query": e.query,
             "expected_filename": e.expected_filename,
             "results": json.loads(e.results_json or "{}"),
             "created_at": e.created_at.isoformat()} for e in evs]


@router.get("/api/evaluation/summary")
def evaluation_summary(db: Session = Depends(get_db)):
    """Aggregate MRR / hit rates over all stored evaluations, per DB."""
    evs = db.query(Evaluation).all()
    if not evs:
        return {"count": 0, "per_db": {},
                "recommendation": "評価データがまだありません"}
    agg = {n: {"rr": [], "hit1": 0, "hit3": 0, "hit5": 0,
               "latency": [], "n": 0} for n in DB_NAMES}
    for e in evs:
        results = json.loads(e.results_json or "{}")
        for name, r in results.items():
            if name not in agg or "error" in r:
                continue
            a = agg[name]
            a["n"] += 1
            a["rr"].append(r.get("reciprocal_rank", 0.0))
            a["hit1"] += 1 if r.get("hit@1") else 0
            a["hit3"] += 1 if r.get("hit@3") else 0
            a["hit5"] += 1 if r.get("hit@5") else 0
            a["latency"].append(r.get("latency_ms", 0))
    per_db = {}
    for name, a in agg.items():
        if a["n"] == 0:
            continue
        per_db[name] = {
            "evaluations": a["n"],
            "MRR": round(sum(a["rr"]) / a["n"], 4),
            "hit_rate@1": round(a["hit1"] / a["n"], 4),
            "hit_rate@3": round(a["hit3"] / a["n"], 4),
            "hit_rate@5": round(a["hit5"] / a["n"], 4),
            "avg_latency_ms": round(sum(a["latency"]) / a["n"], 1),
        }
    best = max(per_db.items(),
               key=lambda kv: (kv[1]["MRR"], -kv[1]["avg_latency_ms"]),
               default=(None, None))[0]
    return {"count": len(evs), "per_db": per_db,
            "recommendation": (f"MRRとレイテンシの総合評価では {best} が最良です"
                               if best else "評価データ不足")}
