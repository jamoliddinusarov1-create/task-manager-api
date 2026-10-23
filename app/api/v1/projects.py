"""
Shaxsiy loyihalar (Projects) API yo'llari.
NIMA UCHUN KERAK:
- Foydalanuvchining shaxsiy loyihalarini to'liq boshqarish (CRUD);
- Egalik va ruxsatlarni serverda tekshirish (boshqa foydalanuvchiga tegishli loyihaga 404 qaytarish);
- Ichida vazifasi bor loyihani o'chirishni 409 Conflict bilan rad etish.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.crud.crud_project import (
    create_project,
    get_projects,
    get_project_by_id,
    update_project,
    delete_project
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi shaxsiy loyiha yaratish"
)
def create_new_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Yangi loyiha yaratish.
    Loyiha serverda avtomatik ravishda tokendan olingan `current_user.id` ga bog'lanadi.
    """
    return create_project(db=db, project_in=project_in, user_id=current_user.id)


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="Foydalanuvchining barcha loyihalari ro'yxatini olish (Pagination bilan)"
)
def list_projects(
    skip: int = Query(0, ge=0, description="Tashlab ketiladigan elementlar soni"),
    limit: int = Query(20, ge=1, le=100, description="Bir sahifadagi elementlar soni"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Faqat tizimga kirgan foydalanuvchining o'z loyihalari ro'yxatini qaytaradi."""
    projects = get_projects(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Loyiha tafsilotini ID bo'yicha olish"
)
def get_project_details(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ID bo'yicha loyihani olish.
    Agar loyiha mavjud bo'lmasa yoki boshqa birovga tegishli bo'lsa -> 404 Not Found.
    """
    project = get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Loyihani tahrirlash"
)
def update_project_by_id(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Loyihaning nomi yoki tavsifini yangilash."""
    project = get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    return update_project(db=db, db_project=project, project_in=project_in)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Loyihani o'chirish (Agar vazifasi bo'lsa 409 xatolik)"
)
def delete_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    IMTIHON TALABI BO'YICHA:
    Ichida vazifasi bor loyihani o'chirish 409 Conflict bilan rad etilsin.
    """
    project = get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    delete_project(db=db, db_project=project)
    return None
