"""Vectorize API — chunk + embed + register to ALL 3 vector DBs."""
import os

from database import DocumentVersion, get_db, get_setting
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.bedrock import embed_texts
from services.textproc import chunk_text, extract_text
from services.vectordb import all_dbs
from sqlalchemy.orm import Session

router = APIRouter()


class VectorizeRequest(BaseModel):
    version_id: int
    chunk_size: int | None = None      # default from settings
    chunk_overlap: int | None = None


@router.post("/api/vectorize")
def vectorize(req: VectorizeRequest, db: Session = Depends(get_db)):
    ver = db.get(DocumentVersion, req.version_id)
    if not ver:
        raise HTTPException(404, "version not found")

    chunk_size = req.chunk_size or int(get_setting(db, "chunk_size", "512"))
    overlap = (req.chunk_overlap if req.chunk_overlap is not None
               else int(get_setting(db, "chunk_overlap", "50")))
    if chunk_size < 32 or chunk_size > 8000:
        raise HTTPException(400, "chunk_size must be 32..8000")

    if not os.path.exists(ver.file_path):
        raise HTTPException(500, "stored file missing")
    with open(ver.file_path, "rb") as f:
        data = f.read()

    ver.status = "vectorizing"
    db.commit()
    try:
        text = extract_text(ver.document.filename, data)
        pieces = chunk_text(text, chunk_size, overlap)
        if not pieces:
            raise HTTPException(400, "no text extracted from file")
        embeddings = embed_texts(pieces)
        chunks = [dict(document_version_id=ver.id, chunk_index=i,
                       content=p, embedding=e,
                       filename=ver.document.filename, version=ver.version,
                       visibility_level=ver.visibility_level)
                  for i, (p, e) in enumerate(zip(pieces, embeddings))]
        results = {}
        for vdb in all_dbs():
            vdb.delete_by_docver(ver.id)  # re-vectorize safe
            vdb.upsert(chunks)
            results[vdb.name] = len(chunks)
        # this version becomes the active one for its document
        for sibling in ver.document.versions:
            sibling.is_active = 1 if sibling.id == ver.id else 0
        ver.status = "vectorized"
        ver.chunk_size = chunk_size
        ver.chunk_overlap = overlap
        ver.chunk_count = len(chunks)
        db.commit()
        return {"version_id": ver.id, "filename": ver.document.filename,
                "version": ver.version, "chunk_size": chunk_size,
                "chunk_overlap": overlap, "chunks": len(chunks),
                "registered_dbs": results, "status": "vectorized"}
    except HTTPException:
        ver.status = "failed"
        db.commit()
        raise
    except Exception as e:
        ver.status = "failed"
        db.commit()
        raise HTTPException(500, f"vectorization failed: {e}")
