from fastapi import APIRouter, status
from sqlalchemy import text

from app.database.session import SessionLocal
from app.cache import cache_redis


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/live")
async def liveness():

    return {
        "status": "ok",
    }


@router.get("/ready")
async def readiness():

    checks = {}

    # Database
    try:
        db = SessionLocal()

        db.execute(text("SELECT 1"))

        db.close()

        checks["database"] = {
            "status": "ok"
        }

    except Exception as error:

        checks["database"] = {
            "status": "error",
            "message": str(error),
        }

    # Redis
    try:

        await cache_redis.ping()

        checks["redis"] = {
            "status": "ok"
        }

    except Exception as error:

        checks["redis"] = {
            "status": "error",
            "message": str(error),
        }

    all_healthy = all(
        check["status"] == "ok"
        for check in checks.values()
    )

    return_status = (
        status.HTTP_200_OK
        if all_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=return_status,
        content={
            "status": "ok" if all_healthy else "degraded",
            "checks": checks,
        },
    )
