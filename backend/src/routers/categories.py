from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from src.dependencies.auth import get_current_active_user
from src.dependencies.database import get_db
from src.dependencies.services import get_category_service
from src.models.category import CategoryType
from src.models.user import User
from src.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from src.services.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["🏷️ Categories"])

@router.get(
    "",
    response_model=List[CategoryRead],
    summary="Список категорій користувача"
)
def list_categories(
        type: Optional[CategoryType] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        category_service: CategoryService = Depends(get_category_service)
):
    return category_service.list_categories(db, current_user.id, type)

@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію"
)
def create_category(
        data: CategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        category_service: CategoryService = Depends(get_category_service)
):
    return category_service.create_category(db, current_user.id, data)

@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Перейменувати категорію"
)
def update_category(
        category_id: int,
        data: CategoryUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        category_service: CategoryService = Depends(get_category_service)
):
    return category_service.update_category(db, current_user.id, category_id, data)

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити категорію без транзакцій"
)
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        category_service: CategoryService = Depends(get_category_service)
):
    category_service.delete_category(db, current_user.id, category_id)
