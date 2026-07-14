"""RAG System backend — FastAPI entrypoint.

Issue #7: WEBUIを備えたフラットベクトルRAGの環境
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import BasicAuthMiddleware
from database import init_db
from api import (documents, evaluation, history, search, settings, templates,
                 upload, vectorize)

app = FastAPI(title="RAG System API", version="1.0.0",
              description="WEBUIを備えたフラットベクトルRAG (Issue #7)")

# Client origin is unrestricted per requirement (環境要件3)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])
app.add_middleware(BasicAuthMiddleware)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


for r in (upload, vectorize, search, history, documents, templates,
          evaluation, settings):
    app.include_router(r.router)
