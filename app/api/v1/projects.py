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
    summary="Create a new personal project"
)
def create_new_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a project strictly tied to current authenticated user."""
    return create_project(db=db, project_in=project_in, user_id=current_user.id)


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="List all personal projects with pagination"
)
def list_projects(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all projects belonging exclusively to current user."""
    projects = get_projects(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details by ID"
)
def get_project_details(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve project by ID. Returns 404 if not found or belongs to another user."""
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
    summary="Update project by ID"
)
def update_project_by_id(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project details."""
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
    summary="Delete a project by ID"
)
def delete_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project.
    Business Rule: Ichida vazifasi bor loyihani o'chirish 409 bilan rad etilsin.
    """
    project = get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    delete_project(db=db, db_project=project)
    return None
