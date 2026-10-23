"""
Vazifalar (Tasks) API yo'llari.
NIMA UCHUN KERAK:
- Vazifa qo'shish, ro'yxatini olish, detailini ko'rish, tahrirlash va o'chirish;
- Vazifani bajarilgan deb belgilash yoki qayta ochish (completed_at);
- Vazifalarni loyiha va bajarilganlik holati bo'yicha filtrlash;
- Ustuvorlik (high -> medium -> low) va muddat bo'yicha saralash;
- Muddati o'tgan, bajarilmagan vazifalarni (overdue) chiqarish;
- O'z vazifalari bo'yicha jami, bajarilgan va bajarilmagan sonlarni (statistika) olish.
"""

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
    summary="Foydalanuvchining vazifalari bo'yicha statistikasini olish"
)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    IMTIHON TALABI BO'YICHA:
    O'z vazifalari bo'yicha jami, bajarilgan va bajarilmagan sonlarni olish.
    Boshqa foydalanuvchilar ma'lumotlari hisobga olinmaydi.
    """
    stats = get_task_statistics(db=db, user_id=current_user.id)
    return stats


@router.get(
    "/overdue",
    response_model=List[TaskResponse],
    summary="Muddati o'tgan va hali bajarilmagan vazifalar ro'yxati"
)
def list_overdue_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    IMTIHON TALABI BO'YICHA:
    Overdue: deadline < hozirgi vaqt VA vazifa hali bajarilmagan.
    DIQQAT: Bajarilgan eski vazifa hech qachon overdue ro'yxatiga kirmasin!
    """
    return get_overdue_tasks(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi vazifa yaratish"
)
def create_new_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Yangi vazifa yaratish.
    BIZNES QOIDASI: Vazifa faqat egasining o'z loyihasiga bog'lanishi shart!
    """
    return create_task(db=db, task_in=task_in, user_id=current_user.id)


@router.get(
    "",
    response_model=List[TaskResponse],
    summary="Vazifalar ro'yxatini filtrlash va maxsus saralash bilan olish"
)
def list_user_tasks(
    project_id: Optional[int] = Query(None, description="Loyiha ID si bo'yicha filtrlash"),
    completed: Optional[bool] = Query(None, description="Bajarilganlik holati bo'yicha filtrlash"),
    sort_by: Optional[str] = Query(
        "priority",
        description="Saralash: priority (high->low), priority_asc, deadline (yaqin muddat birinchi), deadline_desc"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    IMTIHON TALABI BO'YICHA:
    Priority alifbo tartibida emas, high -> medium -> low tartibida saralansin.
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
    summary="Vazifa tafsilotini ID bo'yicha olish"
)
def get_task_details(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bitta vazifani olish. Boshqa birovning vazifasiga kirishga urinilsa -> 404 Not Found."""
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
    summary="Vazifani tahrirlash"
)
def update_task_details(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vazifa maydonlarini (nom, tavsif, priority, deadline, loyiha) yangilash."""
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
    summary="Vazifani bajarilgan deb belgilash yoki qayta ochish"
)
def change_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    IMTIHON TALABI BO'YICHA:
    Bajarilganda completed_at o'rnatilsin (hozirgi vaqt); qayta ochilganda tozalansin (null).
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
    summary="Vazifani o'chirish"
)
def delete_task_by_id(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vazifani o'chirish."""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    delete_task(db=db, db_task=task)
    return None
