from fastapi import APIRouter, Depends

from app.models.user import User
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "tier": current_user.tier
    }
