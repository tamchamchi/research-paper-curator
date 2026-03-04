import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, JSON
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from src.db.interfaces.mysql import Base


class Paper(Base):
    __tablename__ = "papers"

    # Core metadata
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    arxiv_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    authors = Column(JSON, nullable=False)
    abstract = Column(MEDIUMTEXT, nullable=False)
    categories = Column(JSON, nullable=False)
    published_date = Column(DateTime(timezone=True), nullable=False, index=True)
    pdf_url = Column(String(1024), nullable=False)

    # Parsed PDF
    raw_text = Column(MEDIUMTEXT, nullable=True)
    sections = Column(JSON, nullable=True)
    references = Column(JSON, nullable=True)

    # PDF processing
    parser_used = Column(String(100), nullable=True)
    parser_metadata = Column(JSON, nullable=True)
    pdf_processed = Column(Boolean, default=False, nullable=False, index=True)
    pdf_processing_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )