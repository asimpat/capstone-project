from fastapi import Depends

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.permission import Permission

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


def get_user_permissions(
    db: Session,
    user_id: str
) -> set[str]:

    result = db.execute(
        select(Permission.name)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id
        )
        .where(
            UserRole.user_id == user_id
        )
    )

    return set(result.scalars().all())


def require_permission(*required_permissions: str):
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user_permissions = get_user_permissions(
            db,
            current_user.id
        )

        missing_permissions = [
            permission
            for permission in required_permissions
            if permission not in user_permissions
        ]

        if missing_permissions:
            raise APIException(
                status_code=403,
                code="INSUFFICIENT_PERMISSIONS",
                message="Insufficient permissions"
            )

        return current_user

    return permission_dependency
