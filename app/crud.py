import datetime
from sqlalchemy.orm import Session
from app import models, schemas


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
    db_project = models.Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Add to project participants table.
    for user in project.projectParticipants:
        db_project_participant = models.ProjectParticipants(roleId=user.roleId, projectId=db_project.id, userId=user.userId)
        db.add(db_project_participant)
        db.commit()
        db.refresh(db_project_participant)

    response_project_data = schemas.Project(id=db_project.id, name=project.name, description=project.description, projectParticipants=project.projectParticipants)

    return response_project_data


def delete_project(db: Session, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()
    db.delete(db_project)
    db.commit()
    return db_project


def get_project_participants(db: Session, projectId: int):
    return db.query(models.ProjectParticipants).filter(models.ProjectParticipants.projectId == projectId).all()


def update_project_data(db: Session, project: schemas.ProjectDataPatch, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()

    db_project.name = db_project.name if project.name is None else project.name
    db_project.description = db_project.description if project.description is None else project.description

    db.commit()
    db.refresh(db_project)

    response_project_data = schemas.ProjectDataPatchResponse(id=db_project.id, name=db_project.name, description=db_project.description)

    return response_project_data


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


def get_user_role_from_project(db: Session, projectId: int, userId: int):
    return db.query(models.ProjectParticipants)\
        .filter(models.ProjectParticipants.projectId == projectId,
                models.ProjectParticipants.userId == userId)\
        .first()


def get_all_user_roles(db: Session, projectId: int, userId: int):
    return db.query(models.ProjectParticipants)\
        .filter(models.ProjectParticipants.projectId == projectId, 
                models.ProjectParticipants.userId == userId)\
        .all()


# get zgodba by id
def get_story_by_id(db: Session, story_id: int):
    return db.query(models.Story).filter(models.Story.id == story_id).first()


# get zgodba by name
def get_story_by_name(db: Session, name: str):
    return db.query(models.Story).filter(models.Story.name == name).first()


# ustvari novo zgodbo
def create_story(db: Session, story: schemas.StoryCreate):
    db_story = models.Story(name=story.name, storyDescription=story.storyDescription, priority=story.priority, businessValue=story.businessValue, timeEstimate=story.timeEstimate, projectId=story.projectId, isDone=False)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story


# get za vse zgodbe
def get_all_stories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Story).offset(skip).limit(limit).all()


# get za vse zgodbe v projektu
def get_all_stories_in_project(db: Session, project_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Story).filter(models.Story.projectId == project_id).offset(skip).limit(limit).all()


# get za vse zgodbe v projektu z določeno prioriteto
def get_all_stories_in_project_with_priority(db: Session, project_id: int, priority: str, skip: int = 0, limit: int = 100):
    return db.query(models.Story).filter(models.Story.projectId == project_id).filter(models.Story.priority == priority).offset(skip).limit(limit).all()


# update story 
def update_story_generic(db: Session, story: schemas.StoryUpdate, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    # posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.name = db_new_story.name if story.name is None else story.name
    db_new_story.storyDescription = db_new_story.storyDescription if story.storyDescription is None else story.storyDescription
    db_new_story.priority = db_new_story.priority if story.priority is None else story.priority
    db_new_story.businessValue = db_new_story.businessValue if story.businessValue is None else story.businessValue
    db_new_story.timeEstimate = db_new_story.timeEstimate if story.timeEstimate is None else story.timeEstimate
    db_new_story.sprint_id = db_new_story.sprint_id if story.sprint_id is None else story.sprint_id

    db.commit()
    db.refresh(db_new_story)

    return db_new_story


# update only sprint_id
def update_story_sprint_id(db: Session, new_sprint_id: int, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    # posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.sprint_id = db_new_story.sprint_id if new_sprint_id is None else new_sprint_id

    db.commit()
    db.refresh(db_new_story)

    return db_new_story


# update isDone
def update_story_isDone(db: Session, story: schemas.Story, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    # posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.isDone = db_new_story.isDone if story.isDone is None else story.isDone

    db.commit()
    db.refresh(db_new_story)

    return db_new_story


# delete story
def delete_story(db: Session, story_id: int):
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    db.delete(db_story)
    db.commit()
    return db_story


# create test within a story
def create_test(db: Session, test: schemas.AcceptenceTestCreate, story_id: int):
    db_test = models.AcceptenceTest(description=test.description, storyId=story_id)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)

    return db_test


def create_task(db: Session, task: schemas.TaskInput, storyId: int):
    db_task = models.Task(name=task.name, description=task.description, timeEstimate=task.timeEstimate, assigneeUserId=task.assigneeUserId, storyId=storyId)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_all_story_tasks(db: Session, storyId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.Task).filter(models.Task.storyId == storyId).offset(skip).limit(limit).all()


def get_task_by_id(db: Session, taskId: int):
    return db.query(models.Task).filter(models.Task.id == taskId).first()
