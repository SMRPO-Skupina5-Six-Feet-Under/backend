from sqlalchemy.orm import Session
from app import models
from app import schemas


def get_project(db: Session, name: str):
    return db.query(models.Project).filter(models.Project.name == name).first()


def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
