from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import (
    CACHE_TTL,
    cache_get_or_set,
    hash_key,
)
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.permission import Permission


async def get_user_permissions(
    user_id: str,
    db: Session,
):
    key = f"permissions:{hash_key(user_id)}"

    async def fetch_permissions():
        result = db.execute(
            select(Permission.name)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(
                UserRole,
                UserRole.role_id == RolePermission.role_id,
            )
            .where(
                UserRole.user_id == user_id
            )
        )

        permissions = result.scalars().all()

        return list(permissions)

    return await cache_get_or_set(
        key=key,
        ttl_seconds=CACHE_TTL["PERMISSIONS"],
        fetch_fn=fetch_permissions,
    )
