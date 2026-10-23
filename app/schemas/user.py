"""
Foydalanuvchi ma'lumotlarini tekshiruvchi (Validation) Pydantic sxemalari.
NIMA UCHUN KERAK:
- Foydalanuvchi ro'yxatdan o'tayotganda email to'g'riligi va parol uzunligini tekshirish;
- Serverdan javob qaytganda foydalanuvchi parolini (hashed_password) hech qachon chiqarmaslik;
- API ning kiruvchi va chiquvchi ma'lumotlari strukturasini kafolatlash.
"""

import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    """Foydalanuvchining umumiy maydonlari"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Ro'yxatdan o'tish uchun kiruvchi ma'lumotlar sxemasi.
    Parol kamida 6 ta belgidan iborat bo'lishi tekshiriladi.
    """
    password: str = Field(..., min_length=6, description="Parol kamida 6 ta belgidan iborat bo'lishi shart")


class UserLogin(BaseModel):
    """Tizimga kirish (Login) uchun JSON sxemasi"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """
    Foydalanuvchi profili javobi (Response).
    DIQQAT (Imtihon talabi): Ushbu sxemada 'hashed_password' maydoni yo'q,
    shu sababli parol xeshi hech qachon tashqariga sizib chiqmaydi.
    """
    id: int
    is_active: bool
    created_at: datetime.datetime

    # SQLAlchemy modelini Pydantic obyektiga avtomatik o'girish imkonini beradi
    model_config = ConfigDict(from_attributes=True)
