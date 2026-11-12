import logging
import uuid
from datetime import timedelta, datetime, timezone
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from src.config import settings
from src.exceptions import AuthError, BadRequestError, ConflictError, TooManyRequestsError
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.auth import TokenData, TokenResponse
from src.schemas.user import UserCreate, UserUpdate, PasswordChange
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repository: UserRepository, redis_service: RedisService):
        self.user_repository = user_repository
        self.redis_service = redis_service

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _create_token(self, data: dict, expire_delta: timedelta) -> str:
        to_encode = data.copy()
        now = datetime.now(tz=timezone.utc)
        to_encode.update({"exp": now + expire_delta, "iat": now})
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def create_access_token(self, user_id: int, role: str, session_id: str) -> str:
        return self._create_token(
            data={"sub": str(user_id), "role": role, "sid": session_id, "type": "access"},
            expire_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, user_id: int, role: str, session_id: str) -> str:
        return self._create_token(
            data={"sub": str(user_id), "role": role, "sid": session_id, "type": "refresh"},
            expire_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

    def decode_token(self, token: str, expected_type: str = "access") -> TokenData:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError as exc:
            raise AuthError("Невалідний або прострочений токен") from exc

        user_id_str: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        session_id: Optional[str] = payload.get("sid")

        if user_id_str is None or role is None or session_id is None:
            raise AuthError("Токен не містить обов'язкових полів")
        if payload.get("type") != expected_type:
            raise AuthError("Невірний тип токена")

        return TokenData(user_id=int(user_id_str), role=role, session_id=session_id)

    def _start_session(self, user: User) -> TokenResponse:
        session_id = uuid.uuid4().hex
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        self.redis_service.create_session(session_id, user.id, ttl_seconds)

        return TokenResponse(
            access_token=self.create_access_token(user.id, user.role, session_id),
            refresh_token=self.create_refresh_token(user.id, user.role, session_id),
        )

    def register_user(self, db: Session, data: UserCreate, commit: bool = True) -> User:
        email = data.email.lower()

        if self.user_repository.get_by_email(db, email):
            raise ConflictError(f"Користувач з email {email} вже існує")

        user = self.user_repository.create(db, {
            "name": data.name,
            "email": email,
            "password": self.hash_password(data.password),
            "role": "user",
        }, commit=commit)
        logger.info("Новий користувач зареєстрований: id=%d email=%s", user.id, user.email)
        return user

    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(db, email.lower())

        if not user or not self.verify_password(password, user.password):
            raise AuthError("Невірний email або пароль")

        if not user.is_active:
            raise AuthError("Акаунт деактивовано")

        return user

    def login(self, db: Session, email: str, password: str) -> TokenResponse:
        email = email.lower()

        retry_after = self.redis_service.get_login_block_ttl(email)
        if retry_after:
            raise TooManyRequestsError(f"Забагато невдалих спроб. Спробуйте через {retry_after} с", retry_after)

        try:
            user = self.authenticate_user(db, email, password)
        except AuthError:
            self.redis_service.register_failed_login(email)
            raise

        self.redis_service.reset_login_attempts(email)
        return self._start_session(user)

    def refresh_tokens(self, db: Session, refresh_token: str) -> TokenResponse:
        token_data = self.decode_token(refresh_token, expected_type="refresh")

        if self.redis_service.pop_session_user_id(token_data.session_id) != token_data.user_id:
            raise AuthError("Сесію завершено. Увійдіть знову")

        user = self.user_repository.get_by_id(db, token_data.user_id)
        if user is None or not user.is_active:
            raise AuthError("Користувача не знайдено або деактивовано")

        return self._start_session(user)

    def logout(self, session_id: str) -> None:
        self.redis_service.delete_session(session_id)

    def get_user_by_access_token(self, db: Session, token: str) -> tuple[User, TokenData]:
        token_data = self.decode_token(token, expected_type="access")

        if self.redis_service.get_session_user_id(token_data.session_id) != token_data.user_id:
            raise AuthError("Сесію завершено. Увійдіть знову")

        user = self.user_repository.get_by_id(db, token_data.user_id)
        if user is None:
            raise AuthError("Не вдалося перевірити облікові дані")

        return user, token_data

    def update_profile(self, db: Session, user: User, data: UserUpdate) -> User:
        return self.user_repository.update(db, user, data.model_dump())

    def change_password(self, db: Session, user: User, current_session_id: str, data: PasswordChange) -> None:
        # 400, а не 401: інакше фронтенд вирішить, що сесія злетіла
        if not self.verify_password(data.current_password, user.password):
            raise BadRequestError("Поточний пароль невірний")
        if data.current_password == data.new_password:
            raise BadRequestError("Новий пароль збігається з поточним")

        self.user_repository.update(db, user, {"password": self.hash_password(data.new_password)})
        self.redis_service.revoke_user_sessions(user.id, keep_session_id=current_session_id)
        logger.info("Користувач змінив пароль: id=%d", user.id)
