from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://localhost:6379/0"

    # Скільки живе кеш звітів і аналітики, сек
    ANALYTICS_CACHE_TTL_SECONDS: int = 300

    # Захист від перебору пароля: стільки невдалих спроб, потім блок на вікно
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_BLOCK_SECONDS: int = 300

    # Для dev-сервера Vite. У Docker фронтенд ходить через nginx з того ж origin
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # «Сьогодні» і «поточний місяць» рахуються в цьому поясі, а не в UTC сервера
    APP_TIMEZONE: str = "Europe/Kyiv"

    model_config = SettingsConfigDict(
        # .env лежить у корені репозиторію, спільний з docker-compose
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
