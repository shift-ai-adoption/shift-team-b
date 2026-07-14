"""Document management API — list, versions, rollback, delete."""
from database import Document, DocumentVersion, get_db
from fastapi import APIRouter, Depends, HTTPException
from services.vectordb import all_dbs
from sqlalchemy.orm import Session

router = APIRouter()


def _ver_dict(v: DocumentVersion):
    return {"version_id": v.id, "version": v.version, "status": v.status,
            "size_bytes": v.size_bytes, "chunk_size": v.chunk_size,
            "chunk_overlap": v.chunk_overlap, "chunk_count": v.chunk_count,
            "visibility_level": v.visibility_level,
            "is_active": bool(v.is_active),
            "created_at": v.created_at.isoformat()}


@router.get("/api/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.filename).all()
    return [{"document_id": d.id, "filename": d.filename,
             "versions": [_ver_dict(v) for v in d.versions]} for d in docs]


@router.get("/api/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(404, "document not found")
    return {"document_id": d.id, "filename": d.filename,
            "versions": [_ver_dict(v) for v in d.versions]}


@router.post("/api/documents/{document_id}/rollback")
def rollback(document_id: int, target_version: int,
             db: Session = Depends(get_db)):
    """Make an older vectorized version the active one for search."""
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(404, "document not found")
    target = next((v for v in d.versions if v.version == target_version), None)
    if not target:
        raise HTTPException(404, f"version {target_version} not found")
    if target.status != "vectorized":
        raise HTTPException(400, "target version is not vectorized")
    for v in d.versions:
        v.is_active = 1 if v.id == target.id else 0
    db.commit()
    return {"document_id": d.id, "filename": d.filename,
            "active_version": target.version}


@router.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document, all versions, and their vectors in all 3 DBs."""
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(404, "document not found")
    for v in d.versions:
        for vdb in all_dbs():
            try:
                vdb.delete_by_docver(v.id)
            except Exception:
                pass
        db.delete(v)
    db.delete(d)
    db.commit()
    return {"deleted_document_id": document_id}
