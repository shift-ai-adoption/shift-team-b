"""Search history API."""
import json

from database import SearchHistory, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/api/history")
def list_history(limit: int = 50, offset: int = 0,
                 db: Session = Depends(get_db)):
    q = (db.query(SearchHistory)
         .order_by(SearchHistory.id.desc())
         .offset(offset).limit(limit))
    return [{"id": h.id, "query": h.query, "db_used": h.db_used,
             "role": h.role, "latency_ms": h.latency_ms,
             "rating": h.rating,
             "answer_preview": (h.answer or "")[:120],
             "created_at": h.created_at.isoformat()} for h in q]


@router.get("/api/history/{history_id}")
def get_history(history_id: int, db: Session = Depends(get_db)):
    h = db.get(SearchHistory, history_id)
    if not h:
        raise HTTPException(404, "history not found")
    return {"id": h.id, "query": h.query, "prompt": h.prompt,
            "answer": h.answer, "db_used": h.db_used, "role": h.role,
            "template_id": h.template_id, "top_k": h.top_k,
            "hits": json.loads(h.hits_json or "[]"),
            "latency_ms": h.latency_ms, "rating": h.rating,
            "feedback": h.feedback, "created_at": h.created_at.isoformat()}


class RatingRequest(BaseModel):
    rating: int          # 1..5
    feedback: str | None = None


@router.post("/api/history/{history_id}/rating")
def rate_history(history_id: int, req: RatingRequest,
                 db: Session = Depends(get_db)):
    """Qualitative evaluation: star rating + feedback on a search result."""
    if not 1 <= req.rating <= 5:
        raise HTTPException(400, "rating must be 1..5")
    h = db.get(SearchHistory, history_id)
    if not h:
        raise HTTPException(404, "history not found")
    h.rating = req.rating
    h.feedback = req.feedback
    db.commit()
    return {"id": h.id, "rating": h.rating, "feedback": h.feedback}


@router.delete("/api/history/{history_id}")
def delete_history(history_id: int, db: Session = Depends(get_db)):
    h = db.get(SearchHistory, history_id)
    if not h:
        raise HTTPException(404, "history not found")
    db.delete(h)
    db.commit()
    return {"deleted": history_id}
