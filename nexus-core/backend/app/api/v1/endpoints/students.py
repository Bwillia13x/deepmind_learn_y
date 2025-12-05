"""
Students API endpoints.

CRUD operations for Student records.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Student

router = APIRouter(prefix="/students", tags=["students"])


# === Pydantic Schemas ===


class StudentCreate(BaseModel):
    """Request schema for creating a student."""

    student_code: str = Field(..., min_length=3, max_length=64)
    grade: int = Field(..., ge=0, le=12)
    primary_language: str = Field(default="English", max_length=64)
    school_code: str | None = Field(None, max_length=32)


class StudentResponse(BaseModel):
    """Response schema for a student."""

    id: str
    student_code: str
    grade: int
    primary_language: str
    school_code: str | None = None

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    """Response schema for a list of students."""

    students: list[StudentResponse]
    total: int
    page: int
    page_size: int


class StudentUpdate(BaseModel):
    """Request schema for updating a student."""

    grade: int | None = Field(None, ge=0, le=12)
    primary_language: str | None = Field(None, max_length=64)
    school_code: str | None = Field(None, max_length=32)


# === Endpoints ===


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentResponse:
    """
    Create a new student record.

    Note: student_code should be a hashed identifier, NOT the student's name.
    """
    # Check if student_code already exists
    existing = await db.execute(
        select(Student).where(Student.student_code == student.student_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with code {student.student_code} already exists",
        )

    db_student = Student(
        student_code=student.student_code,
        grade=student.grade,
        primary_language=student.primary_language,
        school_code=student.school_code,
    )
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)

    return StudentResponse.model_validate(db_student)


@router.get("", response_model=StudentListResponse)
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
    grade: int | None = Query(None, ge=0, le=12, description="Filter by grade"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> StudentListResponse:
    """List students with optional filters."""
    query = select(Student)

    if school_code:
        query = query.where(Student.school_code == school_code)
    if grade is not None:
        query = query.where(Student.grade == grade)

    # Count total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get page
    query = query.order_by(Student.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    students = result.scalars().all()

    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{student_code}", response_model=StudentResponse)
async def get_student(
    student_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentResponse:
    """Get a student by their code."""
    result = await db.execute(
        select(Student).where(Student.student_code == student_code)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with code {student_code} not found",
        )

    return StudentResponse.model_validate(student)


@router.patch("/{student_code}", response_model=StudentResponse)
async def update_student(
    student_code: str,
    update: StudentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentResponse:
    """Update a student's information."""
    result = await db.execute(
        select(Student).where(Student.student_code == student_code)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with code {student_code} not found",
        )

    # Apply updates
    if update.grade is not None:
        student.grade = update.grade
    if update.primary_language is not None:
        student.primary_language = update.primary_language
    if update.school_code is not None:
        student.school_code = update.school_code

    await db.commit()
    await db.refresh(student)

    return StudentResponse.model_validate(student)


@router.delete("/{student_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a student and all associated records."""
    result = await db.execute(
        select(Student).where(Student.student_code == student_code)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with code {student_code} not found",
        )

    await db.delete(student)
    await db.commit()
