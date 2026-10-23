"""
Loyihalar (Project) ma'lumotlar bazasi modeli.
NIMA UCHUN KERAK:
- Foydalanuvchining shaxsiy loyihalarini bazada saqlash;
- User bilan Foreign Key (tashqi kalit) orqali bog'lanish;
- Ichidagi vazifalar bilan bog'lanish (Task).
"""

import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Project(Base):
    """
    Loyiha jadvali: 'projects'
    """
    __tablename__ = "projects"

    # Birlamchi kalit (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Loyiha nomi
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Loyiha tavsifi (ixtiyoriy)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Loyiha egasi bo'lgan foydalanuvchining ID si (Tashqi kalit - Foreign Key)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

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

    # Bog'lanishlar:
    # owner: Ushbu loyihaning egasi bo'lgan User
    owner: Mapped["User"] = relationship("User", back_populates="projects")

    # tasks: Ushbu loyihaga biriktirilgan vazifalar ro'yxati
    # DIQQAT: Ichida vazifasi bor loyihani o'chirish biznes qoidasi bo'yicha 409 xatolik qaytarishi shart!
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project")
