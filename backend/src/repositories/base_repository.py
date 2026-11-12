from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        return db.get(self.model, id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return list(db.scalars(select(self.model).offset(skip).limit(limit)).all())

    def create(self, db: Session, obj_in: dict, commit: bool = True) -> ModelType:
        # commit=False — тільки flush, коміт зробить той, хто викликав
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        if not commit:
            db.flush()
            return db_obj
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_many(self, db: Session, objs_in: List[dict]) -> List[ModelType]:
        """Кілька записів одним комітом"""
        db_objs = [self.model(**obj_in) for obj_in in objs_in]
        db.add_all(db_objs)
        db.commit()
        return db_objs

    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[ModelType]:
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class UserOwnedRepository(BaseRepository[ModelType]):
    """Для моделей з полем user_id — дістає записи тільки власника"""

    def get_by_id_for_user(self, db: Session, id: int, user_id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.user_id == user_id)
        return db.execute(stmt).scalar_one_or_none()
