from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ParserType(str, Enum):
    """PDF parser types."""

    DOCLING = "DOCLING"


class PaperSection(BaseModel):
    """Represents a section of a research papers"""

    title: str = Field(..., description="Title of the section")
    content: str = Field(..., description="Text content of the section")
    level: int = Field(
        default=1,
        description="Section hierarchy level (1 for top-level sections, 2 for subsections, etc.)",
    )


class PaperFigure(BaseModel):
    """Represents a figure in a paper."""

    caption: str = Field(..., description="Caption of the figure")
    id: str = Field(..., description="Figure identifier, e.g., 'Figure 1'")


class PaperTable(BaseModel):
    """Represents a table in a paper."""

    caption: str = Field(..., description="Caption of the table")
    id: str = Field(..., description="Table identifier, e.g., 'Table 1'")


class PdfContent(BaseModel):
    """PDF-specific content extracted by parsers."""

    sections: List[PaperSection] = Field(
        default_factory=list, description="Paper sections"
    )
    figures: List[PaperFigure] = Field(
        default_factory=list, description="Figures in the paper"
    )
    tables: List[PaperTable] = Field(
        default_factory=list, description="Tables in the paper"
    )
    raw_text: str = Field(..., description="Full raw text extracted from PDF")
    references: List[str] = Field(
        default_factory=list, description="List of references extracted from PDF"
    )
    parser_used: ParserType = Field(..., description="Parser used to extract content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata from the parser"
    )


class ArxivMetadata(BaseModel):
    """Metadata about the arXiv paper."""

    title: str = Field(..., description="Paper title from arXiv")
    authors: List[str] = Field(..., description="Authors from arXiv")
    abstract: str = Field(..., description="Paper abstract from arXiv")
    arxiv_id: str = Field(..., description="arXiv identifier, e.g., '2101.00001v1'")
    categories: List[str] = Field(..., description="arXiv categories")
    published_date: str = Field(..., description="Date published on arXiv")
    pdf_url: str = Field(..., description="PDF download URL from arXiv")


class ParsedPaper(BaseModel):
    """Represents a fully parsed paper with both arXiv metadata and PDF content."""

    arxiv_metadata: ArxivMetadata = Field(..., description="Metadata from arXiv")
    pdf_content: PdfContent = Field(..., description="Content extracted from PDF")
