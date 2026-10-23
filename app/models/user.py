"""
Foydalanuvchilar (User) ma'lumotlar bazasi modeli.
NIMA UCHUN KERAK:
- Tizimda ro'yxatdan o'tgan har bir foydalanuvchini PostgreSQL da saqlash;
- Email unikalligini (Unique constraint) va indeksatsiyani ta'minlash;
- Foydalanuvchining loyihalari va vazifalari bilan bog'lanishini (Relationship) o'rnatish.
"""

import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


class User(Base):
    """
    Foydalanuvchi jadvali: 'users'
    """
    __tablename__ = "users"

    # Birlamchi kalit (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Email: takrorlanmas (unique=True) va tezkor qidiruv uchun indekslangan (index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Xeshlangan parol: bazada hech qachon ochiq parol saqlanmaydi
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Foydalanuvchining to'liq ismi (ixtiyoriy)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Foydalanuvchi hisobi faol yoki yo'qligi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Yaratilgan va yangilangan vaqti (UTC timezone bilan)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Bog'lanishlar (Relationships):
    # Foydalanuvchi o'chirilsa uning loyihalari va vazifalari ham bog'lanadi
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user")
