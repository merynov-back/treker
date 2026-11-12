from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from src.dependencies.auth import get_current_active_user, get_token_data
from src.dependencies.database import get_db
from src.dependencies.services import get_auth_service, get_category_service
from src.models.user import User
from src.schemas.auth import MessageResponse, TokenResponse, RefreshRequest, TokenData
from src.schemas.user import UserRead, UserCreate, UserUpdate, PasswordChange
from src.services.auth_service import AuthService
from src.services.category_service import CategoryService


router = APIRouter(prefix="/auth", tags=["🔑 Auth"])

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача"
)
def register(
        data: UserCreate,
        db: Session = Depends(get_db),
        auth_service: AuthService = Depends(get_auth_service),
        category_service: CategoryService = Depends(get_category_service)
):
    # Користувач і стандартні категорії — одним комітом
    user = auth_service.register_user(db, data, commit=False)
    category_service.create_default_categories(db, user.id)
    db.refresh(user)
    return user

@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Вхід (email передається в полі username)"
)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
        auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.login(db, email=form_data.username, password=form_data.password)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Оновити пару токенів через refresh-токен"
)
def refresh_token(
        body: RefreshRequest,
        db: Session = Depends(get_db),
        auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.refresh_tokens(db, body.refresh_token)

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Завершити поточну сесію"
)
def logout(
        token_data: TokenData = Depends(get_token_data),
        auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.logout(token_data.session_id)
    return MessageResponse(message="Сесію завершено")

@router.get(
    "/me",
    response_model=UserRead,
    summary="Дані поточного користувача"
)
def get_me(
        current_user: User = Depends(get_current_active_user)
):
    return current_user

@router.patch(
    "/me",
    response_model=UserRead,
    summary="Змінити ім'я"
)
def update_me(
        data: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.update_profile(db, current_user, data)

@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Змінити пароль і завершити інші сесії"
)
def change_password(
        data: PasswordChange,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        token_data: TokenData = Depends(get_token_data),
        auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.change_password(db, current_user, token_data.session_id, data)
    return MessageResponse(message="Пароль змінено. Інші сесії завершено")
