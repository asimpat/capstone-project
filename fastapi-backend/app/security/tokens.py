import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv


load_dotenv()


ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET")
REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")

ALGORITHM = "HS256"


if not ACCESS_SECRET:
    raise RuntimeError("JWT_ACCESS_SECRET is not configured")

if not REFRESH_SECRET:
    raise RuntimeError("JWT_REFRESH_SECRET is not configured")


def generate_access_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user.id,
        "role": user.role,
        "tier": user.tier,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    return jwt.encode(
        payload,
        ACCESS_SECRET,
        algorithm=ALGORITHM,
    )


def generate_refresh_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user.id,
        "role": user.role,
        "tier": user.tier,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7),
    }

    return jwt.encode(
        payload,
        REFRESH_SECRET,
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str):
    return jwt.decode(
        token,
        ACCESS_SECRET,
        algorithms=[ALGORITHM],
    )


def verify_refresh_token(token: str):
    return jwt.decode(
        token,
        REFRESH_SECRET,
        algorithms=[ALGORITHM],
    )
