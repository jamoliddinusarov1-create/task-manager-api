"""
Vazifalar (Task) uchun Pydantic sxemalari.
NIMA UCHUN KERAK:
- Vazifa yaratish, tahrirlash va statusini o'zgartirishda ma'lumotlarni tekshirish;
- Overdue va Completed hisob-kitoblarini Pydantic property orqali oson taqdim etish;
- Statistika endpointi uchun maxsus sxemani (TaskStatsResponse) taqdim etish.
"""

import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.task import TaskPriority


class TaskBase(BaseModel):
    """Vazifaning asosiy umumiy maydonlari"""
    title: str = Field(..., min_length=1, max_length=255, description="Vazifa sarlavhasi")
    description: Optional[str] = Field(None, description="Vazifa haqida to'liq tavsif")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Ustuvorlik: low, medium yoki high")
    deadline: Optional[datetime.datetime] = Field(None, description="Bajarish muddati (UTC timezone)")


class TaskCreate(TaskBase):
    """Yangi vazifa yaratish: project_id ko'rsatilishi shart"""
    project_id: int = Field(..., description="Vazifa biriktiriladigan loyiha ID si")


class TaskUpdate(BaseModel):
    """Vazifani tahrirlash: istalgan maydonni ixtiyoriy o'zgartirish mumkin"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime.datetime] = None
    project_id: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    """Vazifa statusini o'zgartirish (bajarildi / qayta ochildi)"""
    completed: bool = Field(..., description="True: bajarilgan deb belgilash, False: qayta ochish")


class TaskResponse(TaskBase):
    """
    Vazifa haqida to'liq ma'lumot qaytaruvchi sxema.
    """
    id: int
    project_id: int
    user_id: int
    completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @property
    def is_completed(self) -> bool:
        """Vazifa bajarilganmi yoki yo'qligini aniqlovchi hisoblangan maydon"""
        return self.completed_at is not None

    @property
    def is_overdue(self) -> bool:
        """
        Biznes qoidasi:
        Faqat bajarilmagan va muddati o'tib ketgan vazifalar overdue bo'ladi.
        Bajarilgan eski vazifalar hech qachon overdue hisoblanmaydi!
        """
        if self.completed_at is not None:
            return False
        if self.deadline is None:
            return False
        now = datetime.datetime.now(datetime.timezone.utc)
        dl = self.deadline
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=datetime.timezone.utc)
        return dl < now

    model_config = ConfigDict(from_attributes=True)


class TaskStatsResponse(BaseModel):
    """Foydalanuvchining shaxsiy vazifalar statistikasi sxemasi"""
    total: int
    completed: int
    uncompleted: int
    overdue: int
