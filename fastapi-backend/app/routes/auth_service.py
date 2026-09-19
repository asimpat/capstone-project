from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.models.refresh_token import RefreshToken
from app.security.token_hash import hash_token

from app.database.session import get_db
from app.models.user import User
from app.schemas import UserRegister, UserLogin, RefreshTokenRequest
from app.security.hash_password import hash_password, verify_password
from app.security.tokens import generate_access_token, generate_refresh_token, verify_refresh_token
from app.events.emitter import event_emitter
from app.utils.responses import success_response
from app.exceptions import APIException

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post("/register",
             status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):


    existing_user = db.query(User).filter(
        User.email == user_data.email.lower().strip()
    ).first()

    if existing_user:
        raise APIException(
            status_code=409,
            code="EMAIL_ALREADY_EXISTS",
            message="Email already registered"
        )
    hashed_password = hash_password(user_data.password)

    user = User(
        name=user_data.name,
        email=user_data.email.lower().strip(),
        password_hash=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    event_emitter.emit(
        "auth:user-registered",
        {
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }
    )

    return success_response(
        {
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    )


@router.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    email = user_data.email.lower().strip()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        raise APIException(
            status_code=401,
            code="AUTHENTICATION_ERROR",
            message="Invalid credentials"
        )

    if not user.is_active:
        raise APIException(
            status_code=401,
            code="AUTHENTICATION_ERROR",
            message="Invalid credentials"
        )

    password_is_valid = verify_password(
        user_data.password,
        user.password_hash
    )

    if not password_is_valid:
        raise APIException(
            status_code=401,
            code="AUTHENTICATION_ERROR",
            message="Invalid credentials"
        )

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )

    db.add(refresh_token_record)
    db.commit()

    event_emitter.emit(
        "auth:user-logged-in",
        {
            "user_id": user.id,
            "email": user.email
        }
    )

    return success_response(
        {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "tier": user.tier
            }
        }
    )


@router.post("/refresh")
def refresh(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = verify_refresh_token(
            token_data.refresh_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    token_hash = hash_token(
        token_data.refresh_token
    )

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_hash
    ).first()

    if not stored_token:
        raise APIException(
            status_code=401,
            code="INVALID_REFRESH_TOKEN",
            message="Invalid refresh token"
        )

    if stored_token.expires_at < datetime.utcnow():
        db.delete(stored_token)
        db.commit()

        raise APIException(
            status_code=401,
            code="REFRESH_TOKEN_EXPIRED",
            message="Refresh token expired"
        )

    user = db.query(User).filter(
        User.id == stored_token.user_id
    ).first()

    if not user or not user.is_active:
       raise APIException(
           status_code=401,
           code="INVALID_REFRESH_TOKEN",
           message="Invalid refresh token"
       )

    # Rotate the refresh token
    db.delete(stored_token)
    db.flush()

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    new_refresh_token = RefreshToken(
        user_id=user.id,
        token=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    db.add(new_refresh_token)
    db.commit()

    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    )


@router.post("/logout")
def logout(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    token_hash = hash_token(
        token_data.refresh_token
    )

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_hash
    ).first()

    if stored_token:
        db.delete(stored_token)
        db.commit()

    return success_response(
        {
            "message": "Logout successful"
        }
    )
