import json
from typing import Any, Callable
import redis
from pydantic import TypeAdapter
from src.config import settings


class RedisService:
    _SESSION_KEY = "session:{session_id}"
    _USER_SESSIONS_KEY = "user:sessions:{user_id}"
    _CACHE_VERSION_KEY = "cache:version:{user_id}"
    _CACHE_KEY = "cache:{user_id}:v{version}:{name}"
    _LOGIN_ATTEMPTS_KEY = "login:attempts:{email}"

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def ping(self) -> bool:
        return bool(self._client.ping())

    def create_session(self, session_id: str, user_id: int, ttl_seconds: int) -> None:
        user_sessions = self._USER_SESSIONS_KEY.format(user_id=user_id)
        pipe = self._client.pipeline()
        pipe.setex(self._SESSION_KEY.format(session_id=session_id), ttl_seconds, str(user_id))
        pipe.sadd(user_sessions, session_id)
        pipe.expire(user_sessions, ttl_seconds)
        pipe.execute()

    def get_session_user_id(self, session_id: str) -> int | None:
        value = self._client.get(self._SESSION_KEY.format(session_id=session_id))
        return int(value) if value is not None else None

    def pop_session_user_id(self, session_id: str) -> int | None:
        # GETDEL атомарний: з двох паралельних refresh сесію отримає лише один
        value = self._client.getdel(self._SESSION_KEY.format(session_id=session_id))
        if value is None:
            return None
        self._client.srem(self._USER_SESSIONS_KEY.format(user_id=value), session_id)
        return int(value)

    def delete_session(self, session_id: str) -> None:
        self.pop_session_user_id(session_id)

    def revoke_user_sessions(self, user_id: int, keep_session_id: str | None = None) -> None:
        """Завершити всі сесії користувача, крім поточної"""
        user_sessions = self._USER_SESSIONS_KEY.format(user_id=user_id)
        to_revoke = [sid for sid in self._client.smembers(user_sessions) if sid != keep_session_id]
        if not to_revoke:
            return

        pipe = self._client.pipeline()
        pipe.delete(*[self._SESSION_KEY.format(session_id=sid) for sid in to_revoke])
        pipe.srem(user_sessions, *to_revoke)
        pipe.execute()

    def get_login_block_ttl(self, email: str) -> int:
        """0 — вхід дозволено, інакше скільки секунд чекати"""
        key = self._LOGIN_ATTEMPTS_KEY.format(email=email)
        attempts = self._client.get(key)
        if attempts is None or int(attempts) < settings.LOGIN_MAX_ATTEMPTS:
            return 0
        return max(self._client.ttl(key), 1)

    def register_failed_login(self, email: str) -> None:
        key = self._LOGIN_ATTEMPTS_KEY.format(email=email)
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.LOGIN_BLOCK_SECONDS, nx=True)
        pipe.execute()

    def reset_login_attempts(self, email: str) -> None:
        self._client.delete(self._LOGIN_ATTEMPTS_KEY.format(email=email))

    # Кеш звітів версіонується: щоб скинути весь кеш користувача, досить збільшити версію

    def _cache_key(self, user_id: int, name: str) -> str:
        version = self._client.get(self._CACHE_VERSION_KEY.format(user_id=user_id)) or 0
        return self._CACHE_KEY.format(user_id=user_id, version=version, name=name)

    def invalidate_user_cache(self, user_id: int) -> None:
        self._client.incr(self._CACHE_VERSION_KEY.format(user_id=user_id))

    def get_or_compute(self, user_id: int, name: str, adapter: TypeAdapter, compute: Callable[[], Any]) -> Any:
        # Ключ беремо до підрахунку, щоб не записати застарілий результат під нову версію
        key = self._cache_key(user_id, name)

        raw = self._client.get(key)
        if raw is not None:
            return adapter.validate_python(json.loads(raw))

        result = compute()
        self._client.setex(key, settings.ANALYTICS_CACHE_TTL_SECONDS, json.dumps(adapter.dump_python(result, mode="json")))
        return result
