from fastapi import APIRouter, HTTPException, Path, Query

from src.dependencies import SessionDep
from src.repositories.paper import PaperRepository
from src.schemas.arxiv.paper import PaperResponse, PaperSearchResponse

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/", response_model=PaperSearchResponse)
def list_papers(
    db: SessionDep,
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of papers to retrieve"
    ),
    offset: int = Query(default=0, ge=0, description="Number of papers to skip"),
) -> PaperSearchResponse:
    """Get a list of papers with pagination."""
    paper_repo = PaperRepository(db)
    papers = paper_repo.get_all(limit=limit, offset=offset)

    # Get total count for pagination info
    total = paper_repo.get_count()

    return PaperSearchResponse(
        papers=[PaperResponse.model_validate(paper) for paper in papers],
        total=total,
    )


@router.get("/{arxiv_id}", response_model=PaperResponse)
def get_paper_details(
    db: SessionDep,
    arxiv_id: str = Path(..., description="The arXiv ID of the paper to retrieve"),
) -> PaperResponse:
    """Get detailed information about a specific paper by its arXiv ID."""
    paper_repo = PaperRepository(db)
    paper = paper_repo.get_by_arxiv_id(arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperResponse.model_validate(paper)
