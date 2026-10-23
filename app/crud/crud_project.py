from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_in: ProjectCreate, user_id: int) -> Project:
    """Create a project strictly owned by the authenticated user."""
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
    """Retrieve all projects belonging to the specified user with pagination."""
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_project_by_id(db: Session, project_id: int, user_id: int) -> Optional[Project]:
    """Retrieve a project by ID strictly ensuring user ownership."""
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
    """Update project fields."""
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, db_project: Project) -> None:
    """
    Delete a project.
    Business Rule: Ichida vazifasi bor loyihani o'chirish 409 bilan rad etilsin.
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
