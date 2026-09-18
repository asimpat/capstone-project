from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.exceptions import APIException

from app.database.session import get_db
from app.models.user import User
from app.security.tokens import verify_access_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
    except Exception:
        raise APIException(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="Invalid or expired access token"
        )

    if payload.get("type") != "access":
        raise APIException(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="Invalid access token"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise APIException(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="Invalid access token"
        )
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise APIException(
            status_code=401,
            code="USER_NOT_FOUND",
            message="User not found"
        )

    if not user.is_active:
        raise APIException(
            status_code=401,
            code="USER_INACTIVE",
            message="User is inactive"
        )

    return user
