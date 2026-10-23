from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskResponse,
    TaskStatsResponse
)
from app.crud.crud_task import (
    create_task,
    get_tasks,
    get_task_by_id,
    update_task,
    set_task_status,
    delete_task,
    get_overdue_tasks,
    get_task_statistics
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/stats",
    response_model=TaskStatsResponse,
    summary="Get statistics on user's tasks"
)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Business Rule:
    O'z vazifalari bo'yicha jami, bajarilgan va bajarilmagan sonlarni olish.
    Boshqa foydalanuvchilar ma'lumotlari hisoblanmaydi.
    """
    stats = get_task_statistics(db=db, user_id=current_user.id)
    return stats


@router.get(
    "/overdue",
    response_model=List[TaskResponse],
    summary="List overdue, uncompleted tasks"
)
def list_overdue_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Business Rule:
    Overdue: deadline < hozir va vazifa bajarilmagan.
    Bajarilgan eski vazifa overdue ro'yxatiga kirmasligi shart.
    """
    return get_overdue_tasks(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task"
)
def create_new_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task attached to a project owned by current user.
    """
    return create_task(db=db, task_in=task_in, user_id=current_user.id)


@router.get(
    "",
    response_model=List[TaskResponse],
    summary="List tasks with filtering and custom sorting"
)
def list_user_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    completed: Optional[bool] = Query(None, description="Filter by completed status"),
    sort_by: Optional[str] = Query(
        "priority",
        description="Sort: priority (high->low), priority_asc, deadline (earliest first), deadline_desc"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve tasks for current user.
    Business Rule:
    Priority bo'yicha saralash alifbo tartibida emas, high -> medium -> low tartibida bo'lsin.
    """
    return get_tasks(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        completed=completed,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get single task details"
)
def get_task_details(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve task details strictly verifying ownership."""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task"
)
def update_task_details(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task fields."""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    return update_task(db=db, db_task=task, task_in=task_in, user_id=current_user.id)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Mark task as completed or reopen"
)
def change_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Business Rule:
    Bajarilganda completed_at o'rnatilsin; qayta ochilganda tozalansin (None).
    """
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    return set_task_status(db=db, db_task=task, completed=status_in.completed)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task"
)
def delete_task_by_id(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task."""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    delete_task(db=db, db_task=task)
    return None
