"""Settings API — chunk size candidates and editable values."""
from database import ROLE_LEVELS, Setting, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()

EDITABLE = {"chunk_size", "chunk_overlap", "top_k"}


@router.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    rows = {s.key: s.value for s in db.query(Setting).all()}
    return {
        "chunk_size": int(rows.get("chunk_size", "512")),
        "chunk_overlap": int(rows.get("chunk_overlap", "50")),
        "top_k": int(rows.get("top_k", "5")),
        "chunk_size_options": [int(x) for x in rows.get(
            "chunk_size_options", "128,256,512,1024,2048").split(",")],
        "chunk_overlap_options": [int(x) for x in rows.get(
            "chunk_overlap_options", "0,50,100,200").split(",")],
        "roles": ROLE_LEVELS,
    }


class SettingsUpdate(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    top_k: int | None = None


@router.put("/api/settings")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "no settings provided")
    if "chunk_size" in updates and not 32 <= updates["chunk_size"] <= 8000:
        raise HTTPException(400, "chunk_size must be 32..8000")
    if "chunk_overlap" in updates and not 0 <= updates["chunk_overlap"] <= 500:
        raise HTTPException(400, "chunk_overlap must be 0..500")
    if "top_k" in updates and not 1 <= updates["top_k"] <= 50:
        raise HTTPException(400, "top_k must be 1..50")
    for k, v in updates.items():
        row = db.get(Setting, k)
        if row:
            row.value = str(v)
        else:
            db.add(Setting(key=k, value=str(v)))
    db.commit()
    return get_settings(db)
