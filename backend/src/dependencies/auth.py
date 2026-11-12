from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status
from src.dependencies.database import get_db
from src.dependencies.services import get_auth_service
from src.models.user import User
from src.schemas.auth import TokenData
from src.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _get_current_session(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        auth_service: AuthService = Depends(get_auth_service)
) -> tuple[User, TokenData]:
    return auth_service.get_user_by_access_token(db, token)


def get_token_data(
        session: tuple[User, TokenData] = Depends(_get_current_session)
) -> TokenData:
    return session[1]


def get_current_active_user(
        session: tuple[User, TokenData] = Depends(_get_current_session)
) -> User:
    user = session[0]
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Акаунт деактивовано"
        )
    return user
