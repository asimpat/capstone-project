from app.routes.documents import router as documents_router

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import APIException
from app.utils.responses import error_response

from app.routes.auth_service import router as auth_router
from app.routes.user_service import router as users_router
import app.events.listeners
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

app = FastAPI()


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
logger = logging.getLogger("__name__")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="NOT_FOUND",
                message="Resource not found",
                details=[]
            )
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code="HTTP_ERROR",
            message=str(exc.detail),
            details=[]
        )
    )

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    details = []

    for error in exc.errors():
        field = ".".join(
            str(location)
            for location in error["loc"]
            if location != "body"
        )

        details.append(
            {
                "field": field,
                "message": error["msg"]
            }
        )

    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details
        )
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unhandled exception occurred",
        exc_info=exc
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=[]
        )
    )

