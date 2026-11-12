from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from starlette import status
from src.dependencies.auth import get_current_active_user
from src.dependencies.database import get_db
from src.dependencies.services import get_transaction_service
from src.models.category import CategoryType
from src.models.user import User
from src.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from src.services.transaction_service import TransactionService


router = APIRouter(prefix="/transactions", tags=["💸 Transactions"])


def transaction_filters(
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category_id: Optional[int] = None,
        type: Optional[CategoryType] = None,
        search: Optional[str] = Query(None, max_length=100, description="Підрядок в описі або назві категорії"),
) -> dict:
    return {
        "date_from": date_from,
        "date_to": date_to,
        "category_id": category_id,
        "type": type,
        "search": search,
    }

@router.get(
    "",
    response_model=List[TransactionRead],
    summary="Список транзакцій з фільтрами (загальна кількість — у X-Total-Count)"
)
def list_transactions(
        response: Response,
        filters: dict = Depends(transaction_filters),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    items, total = transaction_service.list_transactions(db, current_user.id, skip=skip, limit=limit, **filters)
    response.headers["X-Total-Count"] = str(total)
    return items

@router.get(
    "/export",
    summary="Вивантажити транзакції в CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}}
)
def export_transactions(
        filters: dict = Depends(transaction_filters),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    content = transaction_service.export_csv(db, current_user.id, **filters)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )

@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Додати транзакцію"
)
def create_transaction(
        data: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    return transaction_service.create_transaction(db, current_user.id, data)

@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Одна транзакція"
)
def get_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    return transaction_service.get_transaction(db, current_user.id, transaction_id)

@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Змінити транзакцію"
)
def update_transaction(
        transaction_id: int,
        data: TransactionUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    return transaction_service.update_transaction(db, current_user.id, transaction_id, data)

@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити транзакцію"
)
def delete_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        transaction_service: TransactionService = Depends(get_transaction_service)
):
    transaction_service.delete_transaction(db, current_user.id, transaction_id)
