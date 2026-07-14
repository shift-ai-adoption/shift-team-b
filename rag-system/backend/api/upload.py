"""Upload API — file save only (vectorization is a separate step)."""
import os
from datetime import datetime

from database import DocumentVersion, Document, get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

router = APIRouter()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/data/uploads")
ALLOWED_EXT = {".pdf", ".txt", ".md", ".docx"}


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...),
                      visibility_level: int = Form(1),
                      db: Session = Depends(get_db)):
    """Save an uploaded file. Same filename → new version (auto-increment)."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"unsupported file type: {ext} "
                                 f"(allowed: {sorted(ALLOWED_EXT)})")
    if visibility_level not in (1, 2, 3):
        raise HTTPException(400, "visibility_level must be 1..3")

    data = await file.read()
    doc = db.query(Document).filter_by(filename=file.filename).first()
    if not doc:
        doc = Document(filename=file.filename)
        db.add(doc)
        db.flush()
    next_ver = (max((v.version for v in doc.versions), default=0)) + 1

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = os.path.join(UPLOAD_DIR, f"{doc.id}_v{next_ver}_{stamp}{ext}")
    with open(path, "wb") as f:
        f.write(data)

    ver = DocumentVersion(document_id=doc.id, version=next_ver,
                          file_path=path, size_bytes=len(data),
                          status="uploaded", visibility_level=visibility_level)
    db.add(ver)
    db.commit()
    return {"document_id": doc.id, "version_id": ver.id,
            "filename": doc.filename, "version": next_ver,
            "size_bytes": len(data), "status": "uploaded",
            "message": "アップロード完了。ベクトル化は POST /api/vectorize で実行してください。"}
