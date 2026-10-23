"""
Foydalanuvchilar (User) bo'yicha ma'lumotlar bazasi amallari (CRUD).
NIMA UCHUN KERAK:
- Routerni toza saqlash: SQL va ma'lumotlar bazasi so'rovlarini alohida qatlamda (Data Access Layer) jamlash;
- Email bo'yicha qidiruv, yangi foydalanuvchi yaratish va parolni solishtirib tekshirish.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Email bo'yicha foydalanuvchini bazadan qidirib topadi.
    Email kichik harflarga o'tkazilib (lowercase) tekshiriladi.
    """
    stmt = select(User).where(User.email == email.lower().strip())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    ID bo'yicha foydalanuvchini bazadan qidiradi.
    """
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Yangi foydalanuvchini ro'yxatdan o'tkazadi.
    NIMA QILMOQDA:
    - Ochiq parolni bcrypt orqali xeshlaydi;
    - Bazaga yangi User obyektini qo'shadi va saqlaydi (commit);
    - Yangi user obyektini qaytaradi.
    """
    db_user = User(
        email=user_in.email.lower().strip(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Foydalanuvchi login va parolini tekshiradi.
    Agar email topilmasa yoki parol noto'g'ri bo'lsa None qaytaradi.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
