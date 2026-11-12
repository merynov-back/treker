from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.dependencies.auth import get_current_active_user
from src.dependencies.database import get_db
from src.dependencies.services import get_analytics_service
from src.models.category import CategoryType
from src.models.user import User
from src.schemas.analytics import Summary, CategoryTotal, PeriodTotal, GroupBy
from src.services.analytics_service import AnalyticsService


# Без date_from / date_to береться поточний місяць
router = APIRouter(prefix="/analytics", tags=["📊 Analytics"])

@router.get(
    "/summary",
    response_model=Summary,
    summary="Доходи, витрати і баланс за період"
)
def get_summary(
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    return analytics_service.get_summary(db, current_user.id, date_from, date_to)

@router.get(
    "/by-category",
    response_model=List[CategoryTotal],
    summary="Куди йдуть гроші: суми по категоріях"
)
def get_by_category(
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        type: Optional[CategoryType] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    return analytics_service.get_by_category(db, current_user.id, date_from, date_to, type)

@router.get(
    "/by-period",
    response_model=List[PeriodTotal],
    summary="Динаміка доходів і витрат по днях або місяцях"
)
def get_by_period(
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        group_by: GroupBy = GroupBy.DAY,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    return analytics_service.get_by_period(db, current_user.id, date_from, date_to, group_by)
