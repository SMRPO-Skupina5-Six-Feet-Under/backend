import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Date
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


def delete_user(db: Session, userId: int):
    db_user = db.query(models.User).filter(models.User.id == userId).first()
    db_user.userDeleted = True
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: schemas.UserBase):
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    db_user.userName = user.userName
    db_user.firstName = user.firstName
    db_user.lastName = user.lastName
    db_user.email = user.email
    db_user.isAdmin = user.isAdmin
    db.commit()
    db.refresh(db_user)
    return db_user


def edit_check_user_username_exist(db: Session, uUserName: str, uId: int):
    return db.query(models.User).filter(func.lower(models.User.userName) == func.lower(uUserName),
                                        models.User.id != uId).first()


def edit_check_user_email_exist(db: Session, uEmail: str, uId: int):
    return db.query(models.User).filter(func.lower(models.User.email) == func.lower(uEmail),
                                        models.User.id != uId).first()


def check_user_username_exist(db: Session, uUserName: str):
    return db.query(models.User).filter(func.lower(models.User.userName) == func.lower(uUserName)).first()


def check_user_email_exist(db: Session, uEmail: str):
    return db.query(models.User).filter(func.lower(models.User.email) == func.lower(uEmail)).first()


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


def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).filter(models.Project.isAlive).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate):
    # Add to project table.
    db_project = models.Project(name=project.name, description=project.description, documentation="")
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Add to project participants table.
    for user in project.projectParticipants:
        db_project_participant = models.ProjectParticipants(roleId=user.roleId, projectId=db_project.id, userId=user.userId)
        db.add(db_project_participant)
        db.commit()
        db.refresh(db_project_participant)

    response_project_data = schemas.Project(id=db_project.id, name=project.name, description=project.description, documentation="", projectParticipants=project.projectParticipants)

    return response_project_data


def update_project_participants(db: Session, projectId: int, new_participants: List[schemas.ProjectParticipantsInput]):
    # Get current participants situation from DB.
    db_old_participants = get_project_participants(db=db, projectId=projectId)

    # List, where all userId's are stored, for the purposes of recognizing user with double role.
    # Scrum master and developer.
    double_role = []
    for participant in new_participants:
        double_role.append(participant.userId)
    unique_values = set(double_role)
    array_sum = sum(double_role)
    unique_sum = sum(unique_values)
    double_role_user_id = array_sum - unique_sum
    double_user_noticed = 0  # Flag for marking, whether scrum master role has been noticed.

    for new_participant in new_participants:
        update_performed = False  # Flag for marking, whether the UPDATE action has been performed for participant.
        for old_participant in db_old_participants:
            if new_participant.userId == old_participant.userId:
                if update_performed:
                    # Delete (get rid of duplicates because of old entries).
                    db_participant = db.query(models.ProjectParticipants).filter(models.ProjectParticipants.id == old_participant.id).first()
                    if db_participant:
                        db.delete(db_participant)
                        db.commit()
                else:
                    # Handle double role (scrum master and developer) for the same user.
                    if double_user_noticed == 1:
                        double_user_noticed += 1
                    else:
                        if new_participant.userId == double_role_user_id:
                            double_user_noticed += 1
                        # Update.
                        db_participant = db.query(models.ProjectParticipants).filter(models.ProjectParticipants.id == old_participant.id).first()
                        if db_participant:
                            db_participant.roleId = new_participant.roleId
                            db.commit()
                            db.refresh(db_participant)
                            update_performed = True
        if not update_performed:
            # Insert new.
            db_participant = models.ProjectParticipants(roleId=new_participant.roleId, projectId=projectId, userId=new_participant.userId)
            db.add(db_participant)
            db.commit()
            db.refresh(db_participant)

    # List of all new participants, used for deletion.
    new_participants_list = []
    for participant in new_participants:
        new_participants_list.append(participant.userId)

    for participant in db_old_participants:
        if participant.userId not in new_participants_list:
            # Delete (unseen participants).
            db_participant = db.query(models.ProjectParticipants).filter(models.ProjectParticipants.id == participant.id).first()
            db.delete(db_participant)
            db.commit()

    # Retrieve new list of project participants (updated) to make response up to date.
    return db.query(models.ProjectParticipants).filter(models.ProjectParticipants.projectId == projectId).all()


def delete_project(db: Session, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()
    db_project.isAlive = False
    db.commit()
    db.refresh(db_project)
    project_response = schemas.ProjectDataPatchResponse(id=db_project.id, name=db_project.name, description=db_project.description, isAlive=db_project.isAlive)
    return project_response


def get_project_participants(db: Session, projectId: int):
    return db.query(models.ProjectParticipants).filter(models.ProjectParticipants.projectId == projectId).all()


def update_project_data(db: Session, project: schemas.ProjectDataPatch, identifier: int):
    db_project = db.query(models.Project).filter(models.Project.id == identifier).first()

    db_project.name = db_project.name if project.name is None else project.name
    db_project.description = db_project.description if project.description is None else project.description

    db.commit()
    db.refresh(db_project)

    response_project_data = schemas.ProjectDataPatchResponse(id=db_project.id, name=db_project.name, description=db_project.description, isAlive=db_project.isAlive)

    return response_project_data


def get_all_sprints(db: Session, projectId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.Sprint).filter(models.Sprint.projectId == projectId).order_by(models.Sprint.startDate).offset(skip).limit(limit).all()


def get_sprint_by_id(db: Session, sprintId: int):
    return db.query(models.Sprint).filter(models.Sprint.id == sprintId).first()


def create_sprint(db: Session, sprint: schemas.SprintCreate, projectId: int):
    db_sprint = models.Sprint(startDate=sprint.startDate, endDate=sprint.endDate, velocity=sprint.velocity, projectId=projectId)
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)
    return db_sprint


def delete_sprint(db: Session, sprintId: int):
    db_sprint = db.query(models.Sprint).filter(models.Sprint.id == sprintId).first()
    db.delete(db_sprint)
    db.commit()
    return db_sprint


def update_sprint(db: Session, sprint: schemas.SprintPatch, db_sprint: schemas.Sprint):
    db_sprint.startDate = db_sprint.startDate if sprint.startDate is None else sprint.startDate
    db_sprint.endDate = db_sprint.endDate if sprint.endDate is None else sprint.endDate
    db_sprint.velocity = db_sprint.velocity if sprint.velocity is None else sprint.velocity
    db.commit()
    db.refresh(db_sprint)
    return db_sprint


def get_user_role_from_project(db: Session, projectId: int, userId: int):
    return db.query(models.ProjectParticipants)\
        .filter(models.ProjectParticipants.projectId == projectId,
                models.ProjectParticipants.userId == userId)\
        .order_by(models.ProjectParticipants.roleId)\
        .first()


def get_user_role_from_project_descending(db: Session, projectId: int, userId: int):
    return db.query(models.ProjectParticipants)\
        .filter(models.ProjectParticipants.projectId == projectId,
                models.ProjectParticipants.userId == userId)\
        .order_by(models.ProjectParticipants.roleId.desc())\
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


def update_task_assignee_confirm(db: Session, taskId: int, userId: int):
    db_task = db.query(models.Task).filter(models.Task.id == taskId).first()
    db_task.assigneeUserId = userId
    db_task.hasAssigneeConfirmed = True
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_assignee_decline(db: Session, taskId: int):
    db_task = db.query(models.Task).filter(models.Task.id == taskId).first()
    db_task.assigneeUserId = None
    db_task.hasAssigneeConfirmed = False
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_assignee_done(db: Session, taskId: int):
    db_task = db.query(models.Task).filter(models.Task.id == taskId).first()
    db_task.assigneeUserId = None
    db_task.hasAssigneeConfirmed = False
    db_task.isDone = True
    db_task.isActive = False
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task: schemas.TaskInput, db_task: schemas.Task):
    db_task.name = task.name
    db_task.description = task.description
    db_task.timeEstimate = task.timeEstimate
    db_task.assigneeUserId = task.assigneeUserId
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, taskId: int):
    db_task = db.query(models.Task).filter(models.Task.id == taskId).first()
    db.delete(db_task)
    db.commit()
    return db_task


def get_all_project_messages(db: Session, projectId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.Message).filter(models.Message.projectId == projectId).order_by(models.Message.timestamp).offset(skip).limit(limit).all()


def get_my_project_messages(db: Session, projectId: int, userId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.Message).filter(models.Message.projectId == projectId).filter(models.Message.userId == userId).order_by(models.Message.timestamp).offset(skip).limit(limit).all()


def create_message(db: Session, message: schemas.MessageInput, projectId: int, userId: int):
    timestamp = datetime.datetime.now()
    db_message = models.Message(content=message.content, timestamp=timestamp, userId=userId, projectId=projectId)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_documentation(db: Session, documentation: schemas.ProjectDocumentation, db_project: schemas.Project):
    db_project.documentation = documentation.text
    db.commit()
    db.refresh(db_project)
    return db_project.documentation


def set_active_task(db: Session, db_task: models.Task):
    db_task.isActive = True
    db.commit()
    db.refresh(db_task)
    return db_task


def set_inactive_task(db: Session, db_task: models.Task):
    db_task.isActive = False
    db.commit()
    db.refresh(db_task)
    return db_task


def insert_work_progress(db: Session, taskId: int):
    timestamp = datetime.datetime.now()
    db_work_progress = models.WorkProgress(startTimestamp=timestamp, taskId=taskId)
    db.add(db_work_progress)
    db.commit()
    db.refresh(db_work_progress)


def get_work_progress(db: Session, taskId: int):
    stop_time = datetime.datetime.now()
    start_time = db.query(models.WorkProgress).filter(models.WorkProgress.taskId == taskId).order_by(models.WorkProgress.startTimestamp.desc()).first()

    difference_in_hours = int(abs((stop_time - start_time.startTimestamp).total_seconds() / 3600))
    if difference_in_hours <= 0:
        difference_in_hours = 1

    return difference_in_hours


def list_timelogs_by_task_id(db: Session, taskId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.WorkTime).filter(models.WorkTime.taskId == taskId).order_by(models.WorkTime.date.desc()).offset(skip).limit(limit).all()


def list_timelogs_by_task_id_by_user_id(db: Session, taskId: int, userId: int, skip: int = 0, limit: int = 1000):
    return db.query(models.WorkTime).filter(and_(models.WorkTime.taskId == taskId, models.WorkTime.userId == userId)).order_by(models.WorkTime.date.desc()).offset(skip).limit(limit).all()


def update_or_insert_worktime(db: Session, taskId: int, userId: int, workTime: schemas.WorkTimeInput):
    db_worktime = db.query(models.WorkTime).filter(and_(models.WorkTime.taskId == taskId, models.WorkTime.userId == userId, cast(models.WorkTime.date, Date) == workTime.date.date())).first()

    if not db_worktime:
        # Insert new entry under selected date.
        db_worktime = models.WorkTime(date=workTime.date, timeDone=workTime.timeDone, timeRemainingEstimate=workTime.timeRemainingEstimate, userId=userId, taskId=taskId)
        db.add(db_worktime)
        db.commit()
        db.refresh(db_worktime)
    else:
        # Update entry under selected date.
        db_worktime.timeDone = workTime.timeDone
        db_worktime.timeRemainingEstimate = workTime.timeRemainingEstimate
        db.commit()
        db.refresh(db_worktime)

    return db_worktime


def update_worktime(db: Session, taskId: int, taskEstimate: int, userId: int, workDone: int):
    timestamp = datetime.datetime.now()
    db_worktime = db.query(models.WorkTime).filter(and_(models.WorkTime.taskId == taskId, models.WorkTime.userId == userId, cast(models.WorkTime.date, Date) == timestamp.date())).first()

    if not db_worktime:
        # Insert new entry under selected date.
        remaining_estimate_calculation = taskEstimate - workDone
        if remaining_estimate_calculation < 0:
            remaining_estimate_calculation = 0

        db_worktime = models.WorkTime(date=timestamp, timeDone=workDone, timeRemainingEstimate=remaining_estimate_calculation, userId=userId, taskId=taskId)
        db.add(db_worktime)
        db.commit()
        db.refresh(db_worktime)
    else:
        # Update entry under selected date.
        db_current_worktime_calculation = db_worktime.timeDone + workDone
        db_worktime.timeDone = db_current_worktime_calculation
        db.commit()
        db.refresh(db_worktime)

    return db_worktime


def check_any_time_logged(db: Session, taskId: int):
    db_worktime = db.query(models.WorkTime).filter(models.WorkTime.taskId == taskId).first()
    if not db_worktime:
        return False
    return True
