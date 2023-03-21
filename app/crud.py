import datetime
from sqlalchemy.orm import Session
from app import models
from app import schemas


def get_all_users(db: Session):
    return db.query(models.User).all()


def create_user(db: Session, user: schemas.UserCreate):
    new_user = models.User(userName=user.userName, firstName=user.firstName, lastName=user.lastName, email=user.email,
                           isAdmin=user.isAdmin, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return get_UporabnikBase_by_username(db=db, userName=user.userName)


def check_user_username_exist(db: Session, uUserName: str):
    return db.query(models.User).filter(models.User.userName == uUserName).first()


def check_user_email_exist(db: Session, uEmail: str):
    return db.query(models.User).filter(models.User.email == uEmail).first()


def get_UporabnikBase_by_username(db: Session, userName: str):
    return db.query(models.User).filter(models.User.userName == userName).first()


def get_user_by_id(db: Session, identifier: int):
    return db.query(models.User).filter(models.User.id == identifier).first()


def setUserLogInTime(db: Session, userId: int):
    user: schemas.UserBase = db.query(models.User).filter(models.User.id == userId).first()
    if user is not None:
        user.lastLogin = datetime.datetime.now().astimezone()
        db.commit()


def changeUserPassword(db: Session, userId: int, newPassword: str):
    user: schemas.UserBase = db.query(models.User).filter(models.User.id == userId).first()
    if user is not None:
        user.password = newPassword
        db.commit()


def get_project_by_id(db: Session, identifier: int):
    return db.query(models.Project).filter(models.Project.id == identifier).first()


def get_project_by_name(db: Session, name: str):
    return db.query(models.Project).filter(models.Project.name == name).first()


def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate):
    # Add to project table.
    db_project = models.Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Add to project participants table.
    for user in project.projectParticipants:
        db_project_participant = models.ProjectParticipants(roleId=user.roleId, projectId=db_project.id, userId=user.userId)
        db.add(db_project_participant)
        db.commit()
        db.refresh(db_project_participant)

    response_project_data = schemas.Project(name=project.name, id=db_project.id, projectParticipants=project.projectParticipants)

    return response_project_data


def delete_project(db: Session, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()
    db.delete(db_project)
    db.commit()
    return db_project


def get_all_sprints(db: Session, projectId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.Sprint).filter(models.Sprint.projectId == projectId).offset(skip).limit(limit).all()


def get_sprint_by_id(db: Session, sprintId: int):
    return db.query(models.Sprint).filter(models.Sprint.id == sprintId).first()


def create_sprint(db: Session, sprint: schemas.SprintCreate, projectId: int):
    db_sprint = models.Sprint(startDate=sprint.startDate, endDate=sprint.endDate, velocity=sprint.velocity, projectId=projectId)
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)
    return db_sprint
