"""Сесії, кеш і ліміт входу в Redis"""
from pydantic import TypeAdapter

from src.config import settings

int_adapter = TypeAdapter(int)


class TestCache:

    def test_second_call_comes_from_cache(self, redis_service):
        calls = []

        def compute():
            calls.append(1)
            return 42

        assert redis_service.get_or_compute(1, "summary", int_adapter, compute) == 42
        assert redis_service.get_or_compute(1, "summary", int_adapter, compute) == 42
        assert len(calls) == 1

    def test_invalidate_forces_recompute(self, redis_service):
        redis_service.get_or_compute(1, "summary", int_adapter, lambda: 1)
        redis_service.invalidate_user_cache(1)

        assert redis_service.get_or_compute(1, "summary", int_adapter, lambda: 2) == 2

    def test_data_changed_during_compute_is_not_cached_as_fresh(self, redis_service):
        def compute_while_data_changes():
            redis_service.invalidate_user_cache(1)
            return 100

        redis_service.get_or_compute(1, "summary", int_adapter, compute_while_data_changes)

        assert redis_service.get_or_compute(1, "summary", int_adapter, lambda: 200) == 200

    def test_cache_is_per_user(self, redis_service):
        redis_service.get_or_compute(1, "summary", int_adapter, lambda: 1)
        redis_service.invalidate_user_cache(2)

        assert redis_service.get_or_compute(1, "summary", int_adapter, lambda: 999) == 1


class TestSessions:

    def test_pop_session_works_only_once(self, redis_service):
        redis_service.create_session("sid", 7, 60)

        assert redis_service.pop_session_user_id("sid") == 7
        assert redis_service.pop_session_user_id("sid") is None


class TestLoginAttempts:

    def test_blocked_after_max_attempts(self, redis_service):
        for _ in range(settings.LOGIN_MAX_ATTEMPTS - 1):
            redis_service.register_failed_login("a@b.com")
        assert redis_service.get_login_block_ttl("a@b.com") == 0

        redis_service.register_failed_login("a@b.com")
        assert 0 < redis_service.get_login_block_ttl("a@b.com") <= settings.LOGIN_BLOCK_SECONDS

    def test_reset_unblocks(self, redis_service):
        for _ in range(settings.LOGIN_MAX_ATTEMPTS):
            redis_service.register_failed_login("a@b.com")
        redis_service.reset_login_attempts("a@b.com")

        assert redis_service.get_login_block_ttl("a@b.com") == 0

    def test_revoke_other_sessions(self, redis_service):
        redis_service.create_session("current", 7, 60)
        redis_service.create_session("phone", 7, 60)
        redis_service.create_session("stranger", 8, 60)

        redis_service.revoke_user_sessions(7, keep_session_id="current")

        assert redis_service.get_session_user_id("current") == 7
        assert redis_service.get_session_user_id("phone") is None
        assert redis_service.get_session_user_id("stranger") == 8
