"""
Vazifalar (Task) bo'yicha barcha asosiy biznes amallari va ma'lumotlar bazasi so'rovlari (CRUD).
NIMA UCHUN KERAK:
- Vazifa qo'shish, ro'yxatini olish, tahrirlash va o'chirish;
- Imtihonning barcha maxsus biznes qoidalarini bajarish:
  1. Priority bo'yicha maxsus saralash (high -> medium -> low);
  2. Faqat egasining loyihasiga bog'lash tekshiruvi;
  3. Overdue: deadline < hozir va completed_at IS NULL;
  4. Bajarilganda completed_at o'rnatish, qayta ochilganda tozalash;
  5. Shaxsiy statistika (jami, bajarilgan, bajarilmagan, overdue).
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, and_
from fastapi import HTTPException, status

from app.models.task import Task, TaskPriority
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, task_in: TaskCreate, user_id: int) -> Task:
    """
    Yangi vazifa yaratish.
    BIZNES QOIDASI: Vazifa faqat egasining loyihasiga bog'lansin.
    Agar ko'rsatilgan project_id boshqa foydalanuvchiga tegishli bo'lsa, 404 qaytariladi.
    """
    # Berilgan loyiha aynan shu foydalanuvchiga tegishli ekanini tekshiramiz
    project_stmt = select(Project).where(
        Project.id == task_in.project_id,
        Project.user_id == user_id
    )
    project = db.execute(project_stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to attach tasks to it."
        )

    # Muddat (deadline) vaqtini UTC formatga keltirish
    deadline = task_in.deadline
    if deadline and deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    db_task = Task(
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        deadline=deadline,
        project_id=task_in.project_id,
        user_id=user_id,
        completed_at=None
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None,
    completed: Optional[bool] = None,
    sort_by: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[Task]:
    """
    Faqat joriy foydalanuvchiga tegishli vazifalarni filtrlash va saralash bilan olish.
    BIZNES QOIDASI:
    Ustuvorlik bo'yicha saralash alifbo emas, high (1) -> medium (2) -> low (3) tartibida bo'lsin.
    """
    stmt = select(Task).where(Task.user_id == user_id)

    # Loyiha bo'yicha filtrlash
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)

    # Bajarilganlik holati bo'yicha filtrlash
    if completed is True:
        stmt = stmt.where(Task.completed_at.isnot(None))
    elif completed is False:
        stmt = stmt.where(Task.completed_at.is_(None))

    # Priority uchun SQL CASE ifodasi: high=1, medium=2, low=3
    priority_order = case(
        (Task.priority == TaskPriority.HIGH, 1),
        (Task.priority == TaskPriority.MEDIUM, 2),
        (Task.priority == TaskPriority.LOW, 3),
        else_=4
    )

    # Saralash mantiqi
    if sort_by == "priority" or sort_by == "priority_desc":
        # Yuqoridan pastga: high -> medium -> low
        stmt = stmt.order_by(priority_order.asc(), Task.deadline.asc().nulls_last())
    elif sort_by == "priority_asc":
        # Pastdan yuqoriga: low -> medium -> high
        stmt = stmt.order_by(priority_order.desc(), Task.deadline.asc().nulls_last())
    elif sort_by == "deadline" or sort_by == "deadline_asc":
        # Eng yaqin muddat birinchi
        stmt = stmt.order_by(Task.deadline.asc().nulls_last())
    elif sort_by == "deadline_desc":
        # Eng uzoq muddat birinchi
        stmt = stmt.order_by(Task.deadline.desc().nulls_last())
    else:
        # Standart: High priority birinchi, keyin yaratilgan vaqti
        stmt = stmt.order_by(priority_order.asc(), Task.created_at.desc())

    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_task_by_id(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    """Bitta vazifani ID va user_id bo'yicha qat'iy tekshirib olish."""
    stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def update_task(
    db: Session,
    db_task: Task,
    task_in: TaskUpdate,
    user_id: int
) -> Task:
    """Vazifa ma'lumotlarini yangilash."""
    update_data = task_in.model_dump(exclude_unset=True)

    # Agar vazifaning loyihasi (project_id) o'zgartirilayotgan bo'lsa,
    # yangi loyiha ham aynan shu foydalanuvchiga tegishli ekanini tekshiramiz
    if "project_id" in update_data and update_data["project_id"] != db_task.project_id:
        new_project_id = update_data["project_id"]
        project_stmt = select(Project).where(
            Project.id == new_project_id,
            Project.user_id == user_id
        )
        project = db.execute(project_stmt).scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New target project not found or does not belong to you."
            )

    if "deadline" in update_data and update_data["deadline"] is not None:
        dl = update_data["deadline"]
        if dl.tzinfo is None:
            update_data["deadline"] = dl.replace(tzinfo=timezone.utc)

    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def set_task_status(db: Session, db_task: Task, completed: bool) -> Task:
    """
    Vazifani bajarilgan deb belgilash yoki qayta ochish.
    BIZNES QOIDASI: Bajarilganda completed_at hozirgi UTC vaqtga tenglanadi,
    qayta ochilganda esa completed_at = None qilinadi (tozalanadi).
    """
    if completed:
        db_task.completed_at = datetime.now(timezone.utc)
    else:
        db_task.completed_at = None

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: Task) -> None:
    """Vazifani o'chirish."""
    db.delete(db_task)
    db.commit()


def get_overdue_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[Task]:
    """
    BIZNES QOIDASI VA HIMOYADA KO'RSATILADIGAN SSENARIY:
    Overdue: deadline < hozirgi UTC vaqt VA vazifa bajarilmagan (completed_at IS NULL).
    Agar eski vazifa bajarilgan bo'lsa, u hech qachon overdue ro'yxatiga kirmaydi!
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.completed_at.is_(None),
            Task.deadline.isnot(None),
            Task.deadline < now
        )
        .order_by(Task.deadline.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_task_statistics(db: Session, user_id: int) -> dict:
    """
    BIZNES QOIDASI:
    Foydalanuvchining o'z vazifalari bo'yicha jami, bajarilgan,
    bajarilmagan va muddati o'tgan sonlarni bitta SQL aggregatsiya so'rovi bilan olish.
    Boshqa foydalanuvchilar ma'lumotlari hisoblanmaydi.
    """
    now = datetime.now(timezone.utc)

    stmt = select(
        func.count(Task.id).label("total"),
        func.count(case((Task.completed_at.isnot(None), 1))).label("completed"),
        func.count(case((Task.completed_at.is_(None), 1))).label("uncompleted"),
        func.count(
            case((
                and_(
                    Task.completed_at.is_(None),
                    Task.deadline.isnot(None),
                    Task.deadline < now
                ), 1
            ))
        ).label("overdue")
    ).where(Task.user_id == user_id)

    row = db.execute(stmt).one()
    return {
        "total": row.total,
        "completed": row.completed,
        "uncompleted": row.uncompleted,
        "overdue": row.overdue
    }
