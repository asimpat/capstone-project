from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.security.dependencies import get_current_user


def authorize(*allowed_roles: str):
    def authorization_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return current_user

    return authorization_dependency


def require_tier(*allowed_tiers: str):
    def tier_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.tier not in allowed_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient tier"
            )

        return current_user

    return tier_dependency
