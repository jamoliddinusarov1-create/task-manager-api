"""
Loyihalar (Project) uchun Pydantic sxemalari.
NIMA UCHUN KERAK:
- Yangi loyiha yaratish yoki tahrirlashda kelayotgan nom va tavsifni tekshirish;
- Loyiha javobida uning egasi (user_id) va yaratilgan vaqtlarini to'g'ri qaytarish.
"""

import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Loyiha uchun umumiy maydonlar"""
    name: str = Field(..., min_length=1, max_length=200, description="Loyiha nomi")
    description: Optional[str] = Field(None, description="Loyiha tavsifi")


class ProjectCreate(ProjectBase):
    """Yangi loyiha yaratish uchun kiruvchi ma'lumotlar"""
    pass


class ProjectUpdate(BaseModel):
    """Loyihani tahrirlash uchun ma'lumotlar (ixtiyoriy maydonlar)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """
    Loyiha haqida to'liq ma'lumot qaytaruvchi sxema.
    """
    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tasks_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
