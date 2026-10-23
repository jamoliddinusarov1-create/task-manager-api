"""
Vazifalar (Task) ma'lumotlar bazasi modeli.
NIMA UCHUN KERAK:
- Vazifalarning nomi, ustuvorligi (priority), muddati (deadline) va bajarilganlik holatini saqlash;
- Imtihon biznes qoidalarini bazaviy darajada ta'minlash:
  1. Priority: faqat low, medium yoki high;
  2. Deadline va completed_at: UTC timezone bilan aniq hisoblanishi;
  3. Indekslar: saralash va filtrlash tezligini oshirish.
"""

import enum
import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class TaskPriority(str, enum.Enum):
    """
    Vazifaning ustuvorlik darajasi.
    Biznes qoidasi: Saralash alifbo tartibida emas, high -> medium -> low tartibida bo'lishi shart!
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    """
    Vazifa jadvali: 'tasks'
    """
    __tablename__ = "tasks"

    # Birlamchi kalit (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Vazifa sarlavhasi
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Vazifa haqida to'liq ma'lumot
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ustuvorlik (Enum: low, medium, high)
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority_enum", native_enum=False),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )

    # Bajarish muddati (Deadline) - Timezone bilan qabul qilinadi
    deadline: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # Bajarilgan vaqti (completed_at):
    # Biznes qoidasi: Bajarilganda hozirgi vaqt o'rnatiladi, qayta ochilganda null (tozalanadi)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # Tashqi kalitlar (Foreign Keys):
    # project_id: Vazifa qaysi loyihaga tegishli ekani
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    # user_id: Vazifa qaysi foydalanuvchiga tegishli ekani (Multi-tenancy izolyatsiyasi uchun)
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

    # Bog'lanishlar
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")

    # Tezkor qidiruv uchun kompozit indekslar (Composite Indexes)
    __table_args__ = (
        Index("idx_user_project", "user_id", "project_id"),
        Index("idx_user_completed_deadline", "user_id", "completed_at", "deadline"),
    )
