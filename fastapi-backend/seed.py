from datetime import datetime

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole
from app.models.user import User
from app.security.hash_password import hash_password

permission_defs = [
    {
        "name": "documents:create",
        "resource": "documents",
        "action": "create",
        "description": "Upload documents",
    },
    {
        "name": "documents:read",
        "resource": "documents",
        "action": "read",
        "description": "View documents",
    },
    {
        "name": "documents:update",
        "resource": "documents",
        "action": "update",
        "description": "Edit document metadata",
    },
    {
        "name": "documents:delete",
        "resource": "documents",
        "action": "delete",
        "description": "Delete documents",
    },
    {
        "name": "conversations:create",
        "resource": "conversations",
        "action": "create",
        "description": "Start conversations",
    },
    {
        "name": "conversations:read",
        "resource": "conversations",
        "action": "read",
        "description": "View conversations",
    },
    {
        "name": "users:read",
        "resource": "users",
        "action": "read",
        "description": "View user list",
    },
    {
        "name": "users:manage",
        "resource": "users",
        "action": "manage",
        "description": "Manage user accounts",
    },
    {
        "name": "roles:manage",
        "resource": "roles",
        "action": "manage",
        "description": "Manage roles and permissions",
    },
]


def seed_permissions(db):
    permissions = {}

    for data in permission_defs:
        result = db.execute(
            select(Permission).where(
                Permission.name == data["name"]
            )
        )

        permission = result.scalar_one_or_none()

        if not permission:
            permission = Permission(**data)
            db.add(permission)
            db.flush()

        permissions[data["name"]] = permission

    return permissions


role_defs = [
    {
        "name": "admin",
        "description": "Full system access",
        "is_default": False,
    },
    {
        "name": "member",
        "description": "Standard user",
        "is_default": True,
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "is_default": False,
    },
]


def seed_roles(db):
    roles = {}

    for data in role_defs:
        result = db.execute(
            select(Role).where(
                Role.name == data["name"]
            )
        )

        role = result.scalar_one_or_none()

        if not role:
            role = Role(**data)
            db.add(role)
            db.flush()

        roles[data["name"]] = role

    return roles


role_permissions = {
    "admin": [
        "documents:create",
        "documents:read",
        "documents:update",
        "documents:delete",
        "conversations:create",
        "conversations:read",
        "users:read",
        "users:manage",
        "roles:manage",
    ],

    "member": [
        "documents:create",
        "documents:read",
        "documents:update",
        "conversations:create",
        "conversations:read",
    ],

    "viewer": [
        "documents:read",
        "conversations:read",
    ],
}


def seed_role_permissions(db, roles, permissions):
    for role_name, permission_names in role_permissions.items():

        role = roles[role_name]

        for permission_name in permission_names:

            permission = permissions[permission_name]

            result = db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )

            existing = result.scalar_one_or_none()

            if not existing:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

    db.flush()



seed_users_defs = [
    {
        "name": "System Admin",
        "email": "admin@example.com",
        "password": "Admin@123456",
        "role": "admin",
    },
    {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@123456",
        "role": "member",
    },
]


def seed_users(db, roles):
    users = {}

    for data in seed_users_defs:
        result = db.execute(
            select(User).where(
                User.email == data["email"]
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            user = User(
                name=data["name"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
            )

            db.add(user)
            db.flush()

        users[data["email"]] = user

        role = roles[data["role"]]

        result = db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )

        user_role = result.scalar_one_or_none()

        if not user_role:
            db.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by=None,
                )
            )

    db.flush()

    return users


def seed_rbac(db):
    permissions = seed_permissions(db)

    roles = seed_roles(db)

    seed_role_permissions(
        db,
        roles,
        permissions
    )

    users = seed_users(db, roles)

    db.commit()

    return users, roles, permissions


if __name__ == "__main__":
    db = SessionLocal()

    try:
        seed_rbac(db)
        print("RBAC and users seeding completed successfully.")

    except Exception as e:
        db.rollback()
        raise
        # print(f"Seeding failed: {e}")

    finally:
        db.close()
