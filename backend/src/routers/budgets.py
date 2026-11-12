from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status
from src.dependencies.auth import get_current_active_user
from src.dependencies.database import get_db
from src.dependencies.services import get_budget_service
from src.models.user import User
from src.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate, BudgetStatus
from src.services.budget_service import BudgetService


router = APIRouter(prefix="/budgets", tags=["🎯 Budgets"])

@router.get(
    "",
    response_model=List[BudgetRead],
    summary="Бюджети на місяць"
)
def list_budgets(
        year: int = Query(..., ge=2000, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    return budget_service.list_budgets(db, current_user.id, year, month)

@router.get(
    "/status",
    response_model=List[BudgetStatus],
    summary="Виконання бюджетів: скільки витрачено і чи перевищено ліміт"
)
def get_budget_status(
        year: int = Query(..., ge=2000, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    return budget_service.get_budget_status(db, current_user.id, year, month)

@router.post(
    "",
    response_model=BudgetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Встановити ліміт"
)
def create_budget(
        data: BudgetCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    return budget_service.create_budget(db, current_user.id, data)

@router.post(
    "/copy-previous",
    response_model=List[BudgetRead],
    summary="Перенести ліміти з минулого місяця"
)
def copy_previous_budgets(
        year: int = Query(..., ge=2000, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    return budget_service.copy_from_previous_month(db, current_user.id, year, month)

@router.patch(
    "/{budget_id}",
    response_model=BudgetRead,
    summary="Змінити суму ліміту"
)
def update_budget(
        budget_id: int,
        data: BudgetUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    return budget_service.update_budget(db, current_user.id, budget_id, data)

@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити ліміт"
)
def delete_budget(
        budget_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        budget_service: BudgetService = Depends(get_budget_service)
):
    budget_service.delete_budget(db, current_user.id, budget_id)
