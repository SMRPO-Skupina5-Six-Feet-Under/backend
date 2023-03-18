from sqlalchemy.orm import Session
from app import models
from app import schemas


def get_project_by_id(db: Session, identifier: int):
    return db.query(models.Project).filter(models.Project.id == identifier).first()


def get_project_by_name(db: Session, name: str):
    return db.query(models.Project).filter(models.Project.name == name).first()


def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(name=project.name, productOwner=project.productOwner,
                                scrumMaster=project.scrumMaster, developers=project.developers)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()
    db.delete(db_project)
    db.commit()
    return db_project
