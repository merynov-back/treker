from typing import List, Optional
from sqlalchemy.orm import Session
from src.exceptions import NotFoundError, ConflictError
from src.models.category import Category, CategoryType
from src.repositories.category_repository import CategoryRepository
from src.schemas.category import CategoryCreate, CategoryUpdate
from src.services.redis_service import RedisService

# Стартовий набір, щоб новий користувач одразу міг додавати транзакції
DEFAULT_CATEGORIES = [
    ("Зарплата", CategoryType.INCOME),
    ("Подарунки", CategoryType.INCOME),
    ("Інше", CategoryType.INCOME),
    ("Продукти", CategoryType.EXPENSE),
    ("Транспорт", CategoryType.EXPENSE),
    ("Кафе та ресторани", CategoryType.EXPENSE),
    ("Комунальні послуги", CategoryType.EXPENSE),
    ("Здоров'я", CategoryType.EXPENSE),
    ("Розваги", CategoryType.EXPENSE),
    ("Інше", CategoryType.EXPENSE),
]


class CategoryService:
    def __init__(self, category_repository: CategoryRepository, redis_service: RedisService):
        self.category_repository = category_repository
        self.redis_service = redis_service

    def list_categories(self, db: Session, user_id: int, type: Optional[str] = None) -> List[Category]:
        return self.category_repository.get_all_for_user(db, user_id, type)

    def get_category(self, db: Session, user_id: int, category_id: int) -> Category:
        category = self.category_repository.get_by_id_for_user(db, category_id, user_id)
        if category is None:
            raise NotFoundError("Категорію не знайдено")
        return category

    def create_category(self, db: Session, user_id: int, data: CategoryCreate) -> Category:
        if self.category_repository.get_by_name(db, user_id, data.name, data.type):
            raise ConflictError(f"Категорія «{data.name}» вже існує")

        return self.category_repository.create(db, {
            "user_id": user_id,
            "name": data.name,
            "type": data.type,
        })

    def create_default_categories(self, db: Session, user_id: int) -> List[Category]:
        return self.category_repository.create_many(db, [
            {"user_id": user_id, "name": name, "type": type}
            for name, type in DEFAULT_CATEGORIES
        ])

    def update_category(self, db: Session, user_id: int, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get_category(db, user_id, category_id)
        changes = data.model_dump(exclude_unset=True, exclude_none=True)

        # Зміна лише регістру своєї ж назви («кафе» → «Кафе») — не конфлікт
        if "name" in changes and changes["name"].casefold() != category.name.casefold():
            if self.category_repository.get_by_name(db, user_id, changes["name"], category.type):
                raise ConflictError(f"Категорія «{changes['name']}» вже існує")

        category = self.category_repository.update(db, category, changes)
        # Назва категорії є у звітах — скидаємо кеш
        self.redis_service.invalidate_user_cache(user_id)
        return category

    def delete_category(self, db: Session, user_id: int, category_id: int) -> None:
        category = self.get_category(db, user_id, category_id)

        if self.category_repository.has_transactions(db, category.id):
            raise ConflictError("Категорія має транзакції. Спочатку видаліть або перенесіть їх")

        self.category_repository.delete(db, category.id)
        self.redis_service.invalidate_user_cache(user_id)
