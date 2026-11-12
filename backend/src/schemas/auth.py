from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Відповідь при успішній автентифікації"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Дані, витягнуті з JWT-токена"""
    user_id: int
    role: str
    session_id: str

class RefreshRequest(BaseModel):
    """Тіло запиту для оновлення пари токенів"""
    refresh_token: str = Field(..., examples=["eyJhbGci..."])

class MessageResponse(BaseModel):
    """Універсальна відповідь з текстовим повідомленням"""
    message: str = Field(..., examples=["Готово"])
