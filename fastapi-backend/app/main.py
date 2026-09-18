from fastapi import FastAPI

from app.routes.auth_service import router as auth_router
from app.routes.user_service import router as users_router
import app.events.listeners


app = FastAPI()


app.include_router(auth_router)
app.include_router(users_router)