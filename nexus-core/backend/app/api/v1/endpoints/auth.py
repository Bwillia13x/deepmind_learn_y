"""
Authentication API endpoints.

Handles teacher login, registration, and token management.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import Teacher, UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === Pydantic Schemas ===


class TeacherRegister(BaseModel):
    """Request schema for teacher registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    teacher_code: str = Field(..., min_length=3, max_length=64)
    school_code: str | None = Field(None, max_length=32)


class TeacherLogin(BaseModel):
    """Request schema for teacher login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    teacher_id: str
    teacher_code: str
    role: UserRole


class TeacherProfile(BaseModel):
    """Response schema for teacher profile."""

    id: str
    email: str
    teacher_code: str
    school_code: str | None
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Request schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# === Helper Functions ===


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expiration_hours)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


# === Endpoints ===


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_teacher(
    data: TeacherRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Register a new teacher account.

    Creates a new teacher record and returns an access token.
    """
    # Check if email already exists
    existing_email = await db.execute(
        select(Teacher).where(Teacher.email == data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check if teacher_code already exists
    existing_code = await db.execute(
        select(Teacher).where(Teacher.teacher_code == data.teacher_code)
    )
    if existing_code.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher code already in use",
        )

    # Create new teacher
    hashed_password = get_password_hash(data.password)

    teacher = Teacher(
        email=data.email,
        teacher_code=data.teacher_code,
        school_code=data.school_code,
        role=UserRole.TEACHER,
    )
    # Store password hash (need to add field to model)
    teacher.password_hash = hashed_password  # type: ignore

    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)

    # Generate token
    access_token = create_access_token(
        data={"sub": teacher.teacher_code, "role": teacher.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
        teacher_id=teacher.id,
        teacher_code=teacher.teacher_code,
        role=teacher.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: TeacherLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Authenticate a teacher and return an access token.
    """
    # Find teacher by email
    result = await db.execute(
        select(Teacher).where(Teacher.email == data.email)
    )
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    password_hash = getattr(teacher, "password_hash", None)
    if not password_hash or not verify_password(data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = create_access_token(
        data={"sub": teacher.teacher_code, "role": teacher.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
        teacher_id=teacher.id,
        teacher_code=teacher.teacher_code,
        role=teacher.role,
    )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    OAuth2 compatible token endpoint.

    Accepts form data with username (email) and password.
    """
    # Find teacher by email (username field)
    result = await db.execute(
        select(Teacher).where(Teacher.email == form_data.username)
    )
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    password_hash = getattr(teacher, "password_hash", None)
    if not password_hash or not verify_password(form_data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = create_access_token(
        data={"sub": teacher.teacher_code, "role": teacher.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
        teacher_id=teacher.id,
        teacher_code=teacher.teacher_code,
        role=teacher.role,
    )


@router.get("/me", response_model=TeacherProfile)
async def get_current_teacher_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Teacher, Depends(__import__("app.api.deps", fromlist=["require_auth"]).require_auth)],
) -> TeacherProfile:
    """
    Get the current authenticated teacher's profile.
    """
    return TeacherProfile.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Teacher, Depends(__import__("app.api.deps", fromlist=["require_auth"]).require_auth)],
) -> dict[str, str]:
    """
    Change the current teacher's password.
    """
    # Verify current password
    password_hash = getattr(current_user, "password_hash", None)
    if not password_hash or not verify_password(data.current_password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.password_hash = get_password_hash(data.new_password)  # type: ignore
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout() -> dict[str, str]:
    """
    Logout endpoint.

    Note: With JWT tokens, logout is primarily handled client-side by
    discarding the token. This endpoint exists for API completeness.
    """
    return {"message": "Successfully logged out"}
