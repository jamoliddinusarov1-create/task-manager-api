"""
JWT Token ma'lumotlari uchun Pydantic sxemalari.
NIMA UCHUN KERAK:
- Login qilganda qaytariladigan access_token formatini belgilash;
- Token ichidagi shifrlangan ma'lumotlarni (payload: sub, exp) o'qish.
"""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """
    Login muvaffaqiyatli bo'lganda mijozga qaytariladigan JWT token formati.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    JWT tokenni deshifrlash (decode) paytida uning ichidagi ma'lumotlar sxemasi.
    sub: Foydalanuvchining ID si (Subject)
    exp: Tokenning amal qilish muddati tugash vaqti (Expiration timestamp)
    """
    sub: Optional[str] = None
    exp: Optional[int] = None
