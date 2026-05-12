# sap/api/demo/auth.py
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.model import User
from app.core.auth_dependencies import (
    bearer_scheme,
    _extract_token,
    _decode,
    _extract_user_id,
)

def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    token = _extract_token(request, creds)
    if not token:
        return None

    try:
        payload = _decode(token)
        user_id = _extract_user_id(payload)
        return db.get(User, user_id)
    except Exception:
        return None
