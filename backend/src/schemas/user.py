from datetime import datetime
from typing import Annotated
from pydantic import AfterValidator, BaseModel, Field, EmailStr


def _fits_bcrypt(value: str) -> str:
    # bcrypt враховує лише перші 72 байти
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Пароль задовгий: максимум 72 байти (≈36 символів кирилицею)")
    return value

Password = Annotated[str, Field(min_length=8, max_length=72, examples=["StrongPass1!"]), AfterValidator(_fits_bcrypt)]


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Іван Петренко"])
    email: EmailStr = Field(..., examples=["ivan@example.com"])
    password: Password

class UserUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class PasswordChange(BaseModel):
    current_password: str
    new_password: Password

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
