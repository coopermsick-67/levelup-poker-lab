"""Shared API dependencies."""

from typing import Optional

from fastapi import Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

_jose_imports = None


def _decode_token(token: str) -> int:
    """Decode a JWT and return user_id."""
    global _jose_imports
    if _jose_imports is None:
        from jose import JWTError, jwt as _jwt
        _jose_imports = (_jwt, JWTError)
    jwt, JWTError = _jose_imports
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> int:
    """Resolve user_id from Authorization header (preferred) or query param (legacy)."""
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization[7:]
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = _decode_token(raw_token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user_id
