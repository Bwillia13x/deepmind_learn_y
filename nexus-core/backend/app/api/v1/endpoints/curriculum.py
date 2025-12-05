"""
Curriculum API endpoints.

Endpoints for querying Alberta Program of Studies outcomes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import CurriculumOutcome

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


# === Pydantic Schemas ===


class CurriculumOutcomeResponse(BaseModel):
    """Response schema for a curriculum outcome."""

    id: str
    outcome_code: str
    subject: str
    grade: int
    strand: str | None = None
    outcome_text: str
    keywords: str | None = None
    cultural_bridge_hints: str | None = None

    class Config:
        from_attributes = True


class CurriculumOutcomeCreate(BaseModel):
    """Request schema for creating a curriculum outcome."""

    outcome_code: str = Field(..., min_length=1, max_length=32)
    subject: str = Field(..., min_length=1, max_length=64)
    grade: int = Field(..., ge=0, le=12)
    strand: str | None = Field(None, max_length=128)
    outcome_text: str = Field(..., min_length=1)
    keywords: str | None = None
    cultural_bridge_hints: str | None = None


class CurriculumSearchResponse(BaseModel):
    """Response for curriculum search results."""

    outcomes: list[CurriculumOutcomeResponse]
    total: int


# === Endpoints ===


@router.get("", response_model=CurriculumSearchResponse)
async def search_curriculum(
    db: Annotated[AsyncSession, Depends(get_db)],
    subject: str | None = Query(None, description="Filter by subject"),
    grade: int | None = Query(None, ge=0, le=12, description="Filter by grade"),
    keyword: str | None = Query(None, description="Search by keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> CurriculumSearchResponse:
    """
    Search curriculum outcomes.

    Supports filtering by subject, grade, and keyword search.
    """
    query = select(CurriculumOutcome)

    if subject:
        query = query.where(CurriculumOutcome.subject.ilike(f"%{subject}%"))
    if grade is not None:
        query = query.where(CurriculumOutcome.grade == grade)
    if keyword:
        # Search in outcome_text and keywords
        query = query.where(
            CurriculumOutcome.outcome_text.ilike(f"%{keyword}%")
            | CurriculumOutcome.keywords.ilike(f"%{keyword}%")
        )

    # Count total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get page
    query = query.order_by(CurriculumOutcome.grade, CurriculumOutcome.subject)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    outcomes = result.scalars().all()

    return CurriculumSearchResponse(
        outcomes=[CurriculumOutcomeResponse.model_validate(o) for o in outcomes],
        total=total,
    )


@router.get("/{outcome_code}", response_model=CurriculumOutcomeResponse)
async def get_curriculum_outcome(
    outcome_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurriculumOutcomeResponse:
    """Get a specific curriculum outcome by code."""
    result = await db.execute(
        select(CurriculumOutcome).where(CurriculumOutcome.outcome_code == outcome_code)
    )
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curriculum outcome {outcome_code} not found",
        )

    return CurriculumOutcomeResponse.model_validate(outcome)


@router.post("", response_model=CurriculumOutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_curriculum_outcome(
    outcome: CurriculumOutcomeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurriculumOutcomeResponse:
    """
    Create a new curriculum outcome.

    Used by admin/scripts to populate the curriculum database.
    """
    # Check if outcome_code already exists
    existing = await db.execute(
        select(CurriculumOutcome).where(CurriculumOutcome.outcome_code == outcome.outcome_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Curriculum outcome {outcome.outcome_code} already exists",
        )

    db_outcome = CurriculumOutcome(
        outcome_code=outcome.outcome_code,
        subject=outcome.subject,
        grade=outcome.grade,
        strand=outcome.strand,
        outcome_text=outcome.outcome_text,
        keywords=outcome.keywords,
        cultural_bridge_hints=outcome.cultural_bridge_hints,
    )
    db.add(db_outcome)
    await db.commit()
    await db.refresh(db_outcome)

    return CurriculumOutcomeResponse.model_validate(db_outcome)
