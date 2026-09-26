# registration schema

from pydantic import BaseModel, Field
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not any(char.isupper() for char in password):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not any(char.isdigit() for char in password):
            raise ValueError(
                "Password must contain at least one number"
            )

        return password


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    meta: Any = None


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class DocumentListResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=200
    )

    document_id: str | None = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    document_id: str | None
    title: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# MESSAGE SCHEMAS
# ============================================================

class MessageCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000
    )

    document_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    document_id: str | None
    content: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CONVERSATION LIST SCHEMAS
# ============================================================

class LastMessageResponse(BaseModel):
    id: str
    content: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    id: str
    title: str | None
    message_count: int
    last_message: LastMessageResponse | None
    updated_at: datetime

    class Config:
        from_attributes = True
