from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import APIException
from app.utils.responses import error_response

from app.routes.auth_service import router as auth_router
from app.routes.user_service import router as users_router
import app.events.listeners


app = FastAPI()


app.include_router(auth_router)
app.include_router(users_router)


@app.exception_handler(APIException)
async def api_exception_handler(
    request: Request,
    exc: APIException
):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details
        )
    )
