"""Output template API + export of a search result in a chosen format."""
import urllib.parse

from api import role_to_level
from database import OutputTemplate, SearchHistory, get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from services.output_formatter import EXT, FORMATTERS, MIME
from sqlalchemy.orm import Session

router = APIRouter()

VALID_FORMATS = {"markdown", "word", "excel"}


def _tpl_dict(t: OutputTemplate):
    return {"id": t.id, "name": t.name, "format": t.format,
            "description": t.description, "structure": t.structure,
            "min_role_level": t.min_role_level}


class TemplateRequest(BaseModel):
    name: str
    format: str
    description: str | None = None
    structure: str
    min_role_level: int = 1


@router.get("/api/templates")
def list_templates(role: str | None = None, db: Session = Depends(get_db)):
    q = db.query(OutputTemplate).order_by(OutputTemplate.id)
    if role:
        q = q.filter(OutputTemplate.min_role_level <= role_to_level(role))
    return [_tpl_dict(t) for t in q]


@router.post("/api/templates")
def create_template(req: TemplateRequest, db: Session = Depends(get_db)):
    if req.format not in VALID_FORMATS:
        raise HTTPException(400, f"format must be one of {sorted(VALID_FORMATS)}")
    t = OutputTemplate(**req.model_dump())
    db.add(t)
    db.commit()
    return _tpl_dict(t)


@router.put("/api/templates/{template_id}")
def update_template(template_id: int, req: TemplateRequest,
                    db: Session = Depends(get_db)):
    t = db.get(OutputTemplate, template_id)
    if not t:
        raise HTTPException(404, "template not found")
    if req.format not in VALID_FORMATS:
        raise HTTPException(400, f"format must be one of {sorted(VALID_FORMATS)}")
    for k, v in req.model_dump().items():
        setattr(t, k, v)
    db.commit()
    return _tpl_dict(t)


@router.delete("/api/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    t = db.get(OutputTemplate, template_id)
    if not t:
        raise HTTPException(404, "template not found")
    db.delete(t)
    db.commit()
    return {"deleted": template_id}


@router.get("/api/export/{history_id}")
def export_result(history_id: int, format: str = "markdown",
                  db: Session = Depends(get_db)):
    """Download a past search answer as Markdown / Word / Excel."""
    if format not in VALID_FORMATS:
        raise HTTPException(400, f"format must be one of {sorted(VALID_FORMATS)}")
    h = db.get(SearchHistory, history_id)
    if not h:
        raise HTTPException(404, "history not found")
    if not h.answer:
        raise HTTPException(400, "this history entry has no LLM answer")
    data = FORMATTERS[format](h.answer, h.query)
    fname = urllib.parse.quote(f"rag_result_{history_id}.{EXT[format]}")
    return Response(content=data, media_type=MIME[format],
                    headers={"Content-Disposition":
                             f"attachment; filename*=UTF-8''{fname}"})
