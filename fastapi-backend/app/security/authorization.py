from fastapi import Depends

from app.models.user import User
from app.security.dependencies import get_current_user
from app.exceptions import APIException


def authorize(*allowed_roles: str):
    def authorization_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise APIException(
                status_code=403,
                code="INSUFFICIENT_PERMISSIONS",
                message="Insufficient permissions"
            )

        return current_user

    return authorization_dependency


def require_tier(*allowed_tiers: str):
    def tier_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.tier not in allowed_tiers:
            raise APIException(
                status_code=403,
                code="INSUFFICIENT_TIER",
                message="Insufficient tier"
            )

        return current_user

    return tier_dependency
