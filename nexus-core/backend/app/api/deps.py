"""API dependencies for FastAPI routes."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.db.models import Teacher, UserRole

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Handles commit/rollback and cleanup automatically.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for database dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DBSession,
) -> Teacher | None:
    """
    Decode JWT token and return the current authenticated user.

    Returns None if no valid credentials are provided.
    """
    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        teacher_code: str = payload.get("sub")
        if teacher_code is None:
            return None
    except JWTError:
        return None

    result = await db.execute(
        select(Teacher).where(Teacher.teacher_code == teacher_code)
    )
    return result.scalar_one_or_none()


async def require_auth(
    current_user: Annotated[Teacher | None, Depends(get_current_user)],
) -> Teacher:
    """
    Dependency that requires authentication.

    Raises 401 if user is not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin(
    current_user: Annotated[Teacher, Depends(require_auth)],
) -> Teacher:
    """
    Dependency that requires admin role.

    Raises 403 if user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def optional_auth(
    current_user: Annotated[Teacher | None, Depends(get_current_user)],
) -> Teacher | None:
    """
    Dependency that provides optional authentication.

    Returns the user if authenticated, None otherwise.
    Useful for endpoints that behave differently for authenticated users.
    """
    return current_user


async def require_teacher_access(
    current_user: Annotated[Teacher | None, Depends(get_current_user)],
) -> Teacher | None:
    """
    Dependency for teacher-only routes during pilot.

    In development mode (non-production), allows unauthenticated access.
    In production, requires authentication.
    """
    if settings.is_production and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# Type aliases for common dependencies
CurrentUser = Annotated[Teacher | None, Depends(get_current_user)]
AuthenticatedUser = Annotated[Teacher, Depends(require_auth)]
AdminUser = Annotated[Teacher, Depends(require_admin)]
TeacherAccess = Annotated[Teacher | None, Depends(require_teacher_access)]
