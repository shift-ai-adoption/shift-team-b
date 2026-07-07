"""SQLAlchemy models and DB session."""
import os
from datetime import datetime

from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Text, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://rag:ragpass@pgvector:5432/ragdb")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String(512), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    versions = relationship("DocumentVersion", back_populates="document",
                            order_by="DocumentVersion.version")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    file_path = Column(String(1024), nullable=False)
    size_bytes = Column(Integer, default=0)
    status = Column(String(32), default="uploaded")  # uploaded | vectorizing | vectorized | failed
    chunk_size = Column(Integer, nullable=True)
    chunk_overlap = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    visibility_level = Column(Integer, default=1)  # 1=general 2=manager 3=executive
    is_active = Column(Integer, default=1)  # active version used for "latest only" search
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="versions")


class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    prompt = Column(Text)                 # full prompt sent to LLM
    answer = Column(Text)
    db_used = Column(String(64))          # pgvector | chroma | qdrant | compare
    role = Column(String(32))
    template_id = Column(Integer, nullable=True)
    top_k = Column(Integer, default=5)
    hits_json = Column(Text)              # JSON: [{chunk, score, filename, version}]
    latency_ms = Column(Integer)
    rating = Column(Integer, nullable=True)     # 1..5 qualitative
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OutputTemplate(Base):
    __tablename__ = "output_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    format = Column(String(32), nullable=False)   # markdown | word | excel
    description = Column(Text)
    structure = Column(Text)   # instruction for LLM about output structure
    min_role_level = Column(Integer, default=1)   # who can use it
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(128), primary_key=True)
    value = Column(String(512), nullable=False)


class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    expected_filename = Column(String(512), nullable=False)
    results_json = Column(Text)   # per-DB: rank of expected doc, latency, hit@1/3/5, rr
    created_at = Column(DateTime, default=datetime.utcnow)


ROLE_LEVELS = {"general": 1, "manager": 2, "executive": 3}
DEFAULT_SETTINGS = {
    "chunk_size": "512",
    "chunk_overlap": "50",
    "top_k": "5",
    "chunk_size_options": "128,256,512,1024,2048",
    "chunk_overlap_options": "0,50,100,200",
}
DEFAULT_TEMPLATES = [
    dict(name="ビジネスレポート", format="markdown",
         description="見出し・要点・根拠の3部構成のMarkdownレポート",
         structure=("# 見出し（質問の要約）、## 要点（箇条書き3-5点）、"
                    "## 根拠（参照した文書内容の引用と説明）の3部構成で出力する。"),
         min_role_level=1),
    dict(name="エグゼクティブサマリ", format="word",
         description="役員向け1ページ要約 (Word)",
         structure=("役員向けに1ページで完結する要約。結論を最初に、"
                    "次に3点以内の重要ポイント、最後に推奨アクションを記載する。"),
         min_role_level=3),
    dict(name="データ分析表", format="excel",
         description="検索結果を表形式で整理 (Excel)",
         structure=("検索結果を表形式で整理する。各行に項目・内容・出典を含める。"
                    "行は「項目 | 内容 | 出典」の形式で出力する。"),
         min_role_level=1),
]


def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for k, v in DEFAULT_SETTINGS.items():
            if not db.get(Setting, k):
                db.add(Setting(key=k, value=v))
        if db.query(OutputTemplate).count() == 0:
            for t in DEFAULT_TEMPLATES:
                db.add(OutputTemplate(**t))
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_setting(db, key, default=None):
    row = db.get(Setting, key)
    return row.value if row else default
