"""
Loyihalar (Project) bo'yicha ma'lumotlar bazasi amallari (CRUD).
NIMA UCHUN KERAK:
- Loyiha yaratish, ro'yxatini olish, tahrirlash va o'chirish;
- Multi-tenancy (IDOR himoyasi): har bir amal faqat user_id bo'yicha chegaralangan;
- 409 Conflict cheklovi: ichida vazifasi bor loyihani o'chirishni rad etish.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_in: ProjectCreate, user_id: int) -> Project:
    """
    Yangi shaxsiy loyiha yaratish.
    Loyiha qat'iy ravishda joriy foydalanuvchiga (user_id) biriktiriladi.
    """
    db_project = Project(
        name=project_in.name,
        description=project_in.description,
        user_id=user_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[Project]:
    """
    Faqat joriy foydalanuvchiga tegishli loyihalar ro'yxatini pagination bilan olish.
    Boshqa foydalanuvchilarning loyihalari hech qachon chiqmaydi.
    """
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_project_by_id(db: Session, project_id: int, user_id: int) -> Optional[Project]:
    """
    ID va user_id bo'yicha loyihani olish.
    Agar loyiha boshqa foydalanuvchiga tegishli bo'lsa, None qaytadi (va routerda 404 beriladi).
    """
    stmt = (
        select(Project)
        .where(Project.id == project_id, Project.user_id == user_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def update_project(
    db: Session,
    db_project: Project,
    project_in: ProjectUpdate
) -> Project:
    """Loyihaning nomi yoki tavsifini yangilash."""
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, db_project: Project) -> None:
    """
    Loyihani o'chirish.
    DIQQAT (Muhim Biznes Qoidasi):
    Ichida vazifasi (Task) bor loyihani o'chirish 409 Conflict bilan rad etiladi.
    Bog'langan tarix yoki ma'lumotlar tasodifan o'chib ketishidan himoyalaydi.
    """
    task_count_stmt = select(func.count(Task.id)).where(Task.project_id == db_project.id)
    task_count = db.execute(task_count_stmt).scalar_one()

    if task_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete project '{db_project.name}' because it contains "
                f"{task_count} task(s). Delete or reassign tasks first."
            )
        )

    db.delete(db_project)
    db.commit()
