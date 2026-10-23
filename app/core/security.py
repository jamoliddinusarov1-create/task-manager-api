"""
Ushbu modul xavfsizlik, parollarni xeshlash va JWT tokenlarni generatsiya qilish uchun javobgar.
NIMA UCHUN KERAK:
- Foydalanuvchi parollarini bazada ochiq (plain text) saqlamaslik,
  ularni bcrypt orqali qaytarib bo'lmas xesh holatiga keltirish;
- Tizimga kirgan foydalanuvchiga raqamli imzolangan JWT Access Token chiqarib berish;
- Python 3.14 versiyasiga to'liq mos keluvchi zamonaviy `bcrypt` va `PyJWT` kutubxonalaridan foydalanish.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
import jwt

from app.config import settings


def get_password_hash(password: str) -> str:
    """
    Ochiq matn ko'rinishidagi parolni bcrypt algoritmi va salt orqali xeshlaydi.
    NIMA QILMOQDA: Parolni qaytarib bo'lmaydigan xavfsiz xeshga aylantiradi.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Foydalanuvchi kiritgan ochiq parolni bazadagi xesh bilan solishtirib tekshiradi.
    To'g'ri bo'lsa True, noto'g'ri bo'lsa False qaytaradi.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Foydalanuvchi identifikatori (user_id) uchun muddatli JWT access token yaratadi.
    NIMA QILMOQDA:
    - Tokenning amal qilish muddati UTC vaqt bo'yicha hisoblanadi;
    - SECRET_KEY va HS256 algoritmi bilan raqamli imzolanadi.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
