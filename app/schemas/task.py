import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.task import TaskPriority


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Priority: low, medium, or high")
    deadline: Optional[datetime.datetime] = Field(None, description="Task deadline (with timezone)")


class TaskCreate(TaskBase):
    project_id: int = Field(..., description="ID of the user's project to attach task to")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime.datetime] = None
    project_id: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    completed: bool = Field(..., description="True to mark completed, False to reopen")


class TaskResponse(TaskBase):
    id: int
    project_id: int
    user_id: int
    completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def is_overdue(self) -> bool:
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
    total: int
    completed: int
    uncompleted: int
    overdue: int
