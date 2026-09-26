from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User, Organization

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and authenticates user from JWT Bearer token.
    In development mode, if no token is provided, returns or creates default dev admin.
    In production mode, strictly raises 401 Unauthorized.
    """
    if credentials:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated."
            )
        return user

    # Fallback for Development / Demo mode when auth header is omitted
    if settings.APP_MODE in ("development", "demo"):
        # Ensure default organization and analyst user exist
        org = db.query(Organization).filter(Organization.slug == "default").first()
        if not org:
            org = Organization(id="org-default-01", name="Default Enterprise SOC", slug="default")
            db.add(org)
            db.commit()
            db.refresh(org)

        user = db.query(User).filter(User.email == "analyst@sentinelvoice.internal").first()
        if not user:
            from app.core.security import hash_password
            user = User(
                id="user-default-analyst",
                organization_id=org.id,
                email="analyst@sentinelvoice.internal",
                hashed_password=hash_password("SentinelAnalyst2026!"),
                full_name="SOC Lead Analyst",
                role="ADMIN",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    # Strict production requirement
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials required in production mode.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        return current_user
    return role_checker


def get_current_organization(current_user: User = Depends(get_current_user)) -> str:
    return current_user.organization_id
