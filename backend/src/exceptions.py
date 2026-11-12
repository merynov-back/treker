import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette import status

logger = logging.getLogger(__name__)


# Не наслідуємо ValueError: інакше помилки pydantic у нашому ж коді ставали б 400 замість 500

class DomainError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    headers: dict | None = None

class BadRequestError(DomainError):
    pass

class NotFoundError(DomainError):
    """Об'єкт не знайдено або він належить іншому користувачу"""
    status_code = status.HTTP_404_NOT_FOUND

class ConflictError(DomainError):
    """Дублікат або дія, яка ламає цілісність даних"""
    status_code = status.HTTP_409_CONFLICT

class AuthError(DomainError):
    """Невірні облікові дані, токен або сесія"""
    status_code = status.HTTP_401_UNAUTHORIZED
    headers = {"WWW-Authenticate": "Bearer"}

class TooManyRequestsError(DomainError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.headers = {"Retry-After": str(retry_after)}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)}, headers=exc.headers)

    # Два однакові запити одночасно пройшли перевірку в сервісі — другий спіткнеться об unique
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("IntegrityError on %s %s: %s", request.method, request.url.path, exc.orig)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Такий запис уже існує або порушує цілісність даних"}
        )
