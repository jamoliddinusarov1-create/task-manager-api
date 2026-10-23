"""
FastAPI Dependency Injection (Bog'liqliklarni boshqarish) moduli.
NIMA UCHUN KERAK:
- Har bir himoyalangan endpointda foydalanuvchining JWT tokenini avtomatik ushlab tekshirish;
- Muddati o'tgan yoki soxta tokenlarga 401 Unauthorized qaytarish;
- Tokendagi user_id orqali bazadan joriy foydalanuvchini (current_user) topib, endpointga yetkazish.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.crud.crud_user import get_user_by_id

# OAuth2 sxemasi: Swagger UI da "Authorize" tugmasi ishlashi va
# HTTP so'rovlarining "Authorization: Bearer <TOKEN>" sarlavhasidan tokenni o'qish uchun xizmat qiladi
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    JWT Access Tokenni tekshiruvchi va joriy foydalanuvchini qaytaruvchi asosiy Dependency.
    NIMA QILMOQDA:
    1. Tokendagi raqamli imzoni SECRET_KEY bilan tekshiradi;
    2. Token muddati o'tgan bo'lsa (ExpiredSignatureError) -> 401 xatolik beradi;
    3. Agar token buzilgan yoki yaroqsiz bo'lsa -> 401 qaytaradi;
    4. Bazadan foydalanuvchini topadi va faolligini tekshiradi;
    5. Tayyor `current_user` obyektini endpointga taqdim etadi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Tokendagi payloadni ochish
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        # Token amal qilish muddati tugagan holat
        raise token_expired_exception
    except (jwt.PyJWTError, ValueError):
        # Noto'g'ri yoki buzilgan token
        raise credentials_exception

    # Foydalanuvchini bazadan qidirish
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user
