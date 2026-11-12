from fastapi import Depends
from src.dependencies.redis import get_redis_service
from src.repositories.budget_repository import BudgetRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.user_repository import UserRepository
from src.services.analytics_service import AnalyticsService
from src.services.auth_service import AuthService
from src.services.budget_service import BudgetService
from src.services.category_service import CategoryService
from src.services.redis_service import RedisService
from src.services.transaction_service import TransactionService


# Репозиторії

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_category_repository() -> CategoryRepository:
    return CategoryRepository()

def get_transaction_repository() -> TransactionRepository:
    return TransactionRepository()

def get_budget_repository() -> BudgetRepository:
    return BudgetRepository()


# Сервіси

def get_auth_service(
        user_repository: UserRepository = Depends(get_user_repository),
        redis_service: RedisService = Depends(get_redis_service)
) -> AuthService:
    return AuthService(user_repository, redis_service)

def get_category_service(
        category_repository: CategoryRepository = Depends(get_category_repository),
        redis_service: RedisService = Depends(get_redis_service)
) -> CategoryService:
    return CategoryService(category_repository, redis_service)

def get_transaction_service(
        transaction_repository: TransactionRepository = Depends(get_transaction_repository),
        category_repository: CategoryRepository = Depends(get_category_repository),
        redis_service: RedisService = Depends(get_redis_service)
) -> TransactionService:
    return TransactionService(transaction_repository, category_repository, redis_service)

def get_budget_service(
        budget_repository: BudgetRepository = Depends(get_budget_repository),
        category_repository: CategoryRepository = Depends(get_category_repository),
        transaction_repository: TransactionRepository = Depends(get_transaction_repository),
        redis_service: RedisService = Depends(get_redis_service)
) -> BudgetService:
    return BudgetService(budget_repository, category_repository, transaction_repository, redis_service)

def get_analytics_service(
        transaction_repository: TransactionRepository = Depends(get_transaction_repository),
        redis_service: RedisService = Depends(get_redis_service)
) -> AnalyticsService:
    return AnalyticsService(transaction_repository, redis_service)
