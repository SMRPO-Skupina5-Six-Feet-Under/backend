from fastapi import status
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from .database import SessionLocal, engine
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel
import copy
import datetime
from fastapi.middleware.cors import CORSMiddleware  # For middleware.
from app import crud, models, schemas, static  # Local import files.


app = FastAPI(
    title="SMRPO Backend API",
    description="API for backend of SMRPO project.",
)


# "http://localhost",
# "http://localhost:4200",
# tu naj bi se napisalo url iz katerih je dovoljen dostop * naj bi bla za vse
origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# init baze
# models.Base.metadata.drop_all(bind=engine) #če tega ni pol spremembe v classu (dodana polja) ne bojo v bazi
models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Backend is up and running."}


# Login.
class Settings(BaseModel):
    authjwt_secret_key: str = "my_jwt_secret"


@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.post('/login', tags=["Login"])
def login(logInData: schemas.LogInData, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    user_trying_to_login: schemas.UserBase = crud.get_UporabnikBase_by_username(db, logInData.userName)
    if user_trying_to_login is not None and not user_trying_to_login.userDeleted and user_trying_to_login.userName == logInData.userName and user_trying_to_login.password == logInData.password:
        access_token_expires = datetime.timedelta(minutes=90)
        access_token = Authorize.create_access_token(subject=user_trying_to_login.userName, expires_time=access_token_expires)
        __returnUser = copy.deepcopy(user_trying_to_login)
        crud.setUserLogInTime(db, user_trying_to_login.id)
        return {"access_token": access_token, "user": __returnUser}
    else:
        raise HTTPException(status_code=401, detail='Incorrect username or password')


# change pass
@app.post('/users/{userId}/change-password', response_model=schemas.UserBase, tags=["Users"])
def user(userId: int, changePasswordData: schemas.ChangePasswordData, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    #user_name: str = Authorize.get_jwt_subject()  # get username from logged in user - trough Authentication Header
    user_to_change: schemas.UserBase = crud.get_user_by_id(db, userId)
    if user_to_change is None:
        raise HTTPException(status_code=404, detail="User with this id is not present in database.")
    #if user_to_change.userName != user_name:
    #    raise HTTPException(status_code=400, detail="Id and username missmatch")
    if changePasswordData is None or not changePasswordData.newPassword:
        raise HTTPException(status_code=400, detail="New password not provided")
    crud.changeUserPassword(db, userId, changePasswordData.newPassword)
    changedPasswordUser: schemas.UserBase = crud.get_user_by_id(db, userId)
    return changedPasswordUser


@app.get("/users", response_model=List[schemas.UserBase], tags=["Users"])
async def get_all_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.UserBase, tags=["Users"])
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    userNameExists = crud.check_user_username_exist(db, user.userName)
    emailExists = crud.check_user_email_exist(db, user.email)
    if userNameExists:
        raise HTTPException(status_code=400, detail="User with this username already exists.")
    elif emailExists:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    response = crud.create_user(db=db, user=user)
    return response


# Request for 1 user data.
@app.get('/uporabniki/{userName}', response_model=schemas.UserBase, tags=["Users"])
def user(userName: str, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return crud.get_UporabnikBase_by_username(db, userName)

# Update user
@app.put('/users/{userId}', response_model=schemas.UserBase, tags=["Users"])
def update_user_data(userData: schemas.UserBase, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    user_name = Authorize.get_jwt_subject()
    db_current_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    if not db_current_user_data.isAdmin:
        raise HTTPException(status_code=400, detail="Currently logged user must have system administrator rights, in order to perform this action.")

    userNameExists = crud.edit_check_user_username_exist(db, userData.userName, userData.id)
    emailExists = crud.edit_check_user_email_exist(db, userData.email, userData.id)
    if userNameExists:
        raise HTTPException(status_code=400, detail="User with this username already exists.")
    elif emailExists:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    return crud.update_user(db, userData)

# Delete user
@app.delete("/users/{userId}", response_model=schemas.UserBase, tags=["Users"])
async def delete_user(userId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    user_name = Authorize.get_jwt_subject()
    db_current_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    if db_current_user_data.id == userId:
        raise HTTPException(status_code=400, detail="You can't delete yourself.")

    if not db_current_user_data.isAdmin:
        raise HTTPException(status_code=400, detail="Currently logged user must have system administrator rights, in order to perform this action.")

    db_user = crud.get_user_by_id(db=db, identifier=userId)
    if not db_user:
        raise HTTPException(status_code=400, detail="User with given identifier does not exist.")
    return crud.delete_user(db=db, userId=userId)


@app.get("/project/all", response_model=List[schemas.Project], tags=["Projects"])
async def list_all_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_projects = crud.get_all_projects(db, skip=skip, limit=limit)

    response_data: List[schemas.Project] = []
    for project in db_projects:
        db_project_participants = crud.get_project_participants(db=db, projectId=project.id)
        project_data = schemas.Project(id=project.id, name=project.name, description=project.description, documentation=project.documentation, projectParticipants=db_project_participants)
        response_data.append(project_data)

    return response_data


@app.get("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def get_project(identifier: int, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    db_project_participants = crud.get_project_participants(db=db, projectId=identifier)
    response_project_data = schemas.Project(id=db_project.id, name=db_project.name, description=db_project.description, documentation=db_project.documentation, projectParticipants=db_project_participants)

    return response_project_data


@app.post("/project", response_model=schemas.Project, tags=["Projects"])
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Mandatory fields should be checked by frontend (check if they're all fulfilled).

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    if not db_user_data.isAdmin:
        raise HTTPException(status_code=400, detail="Currently logged user must have system administrator rights, in order to perform this action.")

    db_project = crud.get_all_projects(db=db)
    for current_project in db_project:
        if current_project.name.lower() == project.name.lower():
            raise HTTPException(status_code=400, detail="Project with such name already exist.")

    check, message = static.check_project_roles(project.projectParticipants, db)
    if not check:
        raise HTTPException(status_code=400, detail=message)

    return crud.create_project(db=db, project=project)


@app.delete("/project/{identifier}", response_model=schemas.ProjectDataPatchResponse, tags=["Projects"])
async def delete_project(identifier: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # We assume that frontend always serves only projects that actually exist (attribute isAlive set to True).
    # Therefore, there is no need for additional check for project existence on backend.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    if not db_user_data.isAdmin:
        raise HTTPException(status_code=400, detail="Currently logged user must have system administrator rights, in order to perform this action.")

    return crud.delete_project(db=db, identifier=identifier)


@app.get("/project/roles/", tags=["Projects"])
async def get_project_roles() -> list[schemas.ProjectRole]:
    return [
        schemas.ProjectRole(id=1, role="Product owner"),
        schemas.ProjectRole(id=2, role="Scrum master"),
        schemas.ProjectRole(id=3, role="Developer"),
    ]


@app.put("/project/{identifier}/data", response_model=schemas.ProjectDataPatchResponse, tags=["Projects"])
async def update_project_data(identifier: int, project: schemas.ProjectDataPatch, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Both fields are optional.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=identifier, userId=db_user_data.id)

    if not db_user_data.isAdmin:
        if not db_user_project_role:
            raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project or is not system administrator.")

        if db_user_project_role.roleId != 2:
            raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project or system administrator, in order to perform this action.")

    if project.name is not None:
        db_project = crud.get_all_projects(db=db)
        for current_project in db_project:
            if current_project.id != identifier:
                if current_project.name.lower() == project.name.lower():
                    raise HTTPException(status_code=400, detail="Project with such name already exist.")

    return crud.update_project_data(db=db, project=project, identifier=identifier)


@app.put("/project/{identifier}/participants", response_model=List[schemas.ProjectParticipantsInput], tags=["Projects"])
async def update_project_participants(identifier: int, participants: List[schemas.ProjectParticipantsInput], db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=identifier, userId=db_user_data.id)

    if not db_user_data.isAdmin:
        if not db_user_project_role:
            raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project or is not system administrator.")

        if db_user_project_role.roleId != 2:
            raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project or system administrator, in order to perform this action.")

    # Validate new list of all participants.
    check, message = static.check_project_roles(participants, db)
    if not check:
        raise HTTPException(status_code=400, detail=message)

    # Compare and change participants (remove, add, change role).
    return crud.update_project_participants(db=db, projectId=identifier, new_participants=participants)


@app.get("/sprint/{projectId}/all", response_model=List[schemas.Sprint], tags=["Sprints"])
async def list_all_sprints(projectId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")
    return crud.get_all_sprints(db, projectId=projectId, skip=skip, limit=limit)


@app.get("/sprint/{sprintId}", response_model=schemas.Sprint, tags=["Sprints"])
async def get_sprint(sprintId: int, db: Session = Depends(get_db)):
    db_sprint = crud.get_sprint_by_id(db=db, sprintId=sprintId)
    if not db_sprint:
        raise HTTPException(status_code=400, detail="Sprint with given identifier does not exist.")

    return db_sprint


@app.post("/sprint/{projectId}", response_model=schemas.Sprint, tags=["Sprints"])
async def create_sprint(projectId: int, sprint: schemas.SprintCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Mandatory fields should be checked by frontend (check if they're all fulfilled).
    # Make sure that frontend takes care of correct datetime format (e.g. so it is not just random string).

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    if sprint.velocity <= 0:
        raise HTTPException(status_code=400, detail="Sprint velocity cannot be less or equal to zero.")

    start_date_weekend = sprint.startDate.date().weekday()
    if start_date_weekend > 4:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be during the weekend.")

    end_date_weekend = sprint.endDate.date().weekday()
    if end_date_weekend > 4:
        raise HTTPException(status_code=400, detail="Sprint end date cannot be during the weekend.")

    current_date = datetime.date.today()
    if sprint.startDate.date() < current_date:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be earlier than today.")

    if sprint.endDate.date() <= sprint.startDate.date():
        raise HTTPException(status_code=400, detail="Sprint end date cannot be earlier or equal to its start date.")

    all_sprints = crud.get_all_sprints(db, projectId=projectId)
    for current_sprint in all_sprints:
        if sprint.startDate.date() <= current_sprint.startDate.date() <= sprint.endDate.date() or sprint.startDate.date() <= current_sprint.endDate.date() <= sprint.endDate.date():
            raise HTTPException(status_code=400, detail="Given sprint dates overlap with dates of an already existing sprint.")

    return crud.create_sprint(db=db, sprint=sprint, projectId=projectId)


@app.delete("/sprint/{sprintId}", response_model=schemas.Sprint, tags=["Sprints"])
async def delete_sprint(sprintId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Scrum master can delete sprints that haven't started yet.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_sprint = crud.get_sprint_by_id(db=db, sprintId=sprintId)
    if not db_sprint:
        raise HTTPException(status_code=400, detail="Sprint with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_sprint.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    current_date = datetime.date.today()
    if db_sprint.startDate.date() <= current_date:
        raise HTTPException(status_code=400, detail="Only sprint that hasn't started yet or is not currently active can be deleted.")

    return crud.delete_sprint(db=db, sprintId=sprintId)


@app.patch("/sprint/{sprintId}", response_model=schemas.Sprint, tags=["Sprints"])
async def update_sprint(sprintId: int, sprint: schemas.SprintPatch, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # All 3 fields are optional. All required validations (stated below) are applied within endpoint's logic.
    # Scrum master can edit all 3 fields at sprints that haven't started yet.
    # Scrum master can edit only sprint velocity field at sprint that is currently active.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_sprint = crud.get_sprint_by_id(db=db, sprintId=sprintId)
    if not db_sprint:
        raise HTTPException(status_code=400, detail="Sprint with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_sprint.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    current_date = datetime.date.today()

    if db_sprint.startDate.date() < current_date:
        raise HTTPException(status_code=400, detail="Sprints that are already finished cannot be edited.")

    if db_sprint.startDate.date() <= current_date <= db_sprint.endDate.date() and (sprint.startDate is not None or sprint.endDate is not None):
        raise HTTPException(status_code=400, detail="Start and end dates cannot be edited for currently active sprint. They can be edited for sprints that haven't started yet.")

    if sprint.velocity is not None:
        if sprint.velocity <= 0:
            raise HTTPException(status_code=400, detail="Sprint velocity cannot be less or equal to zero.")

    new_start_date = sprint.startDate.date() if sprint.startDate is not None else db_sprint.startDate.date()
    new_end_date = sprint.endDate.date() if sprint.endDate is not None else db_sprint.endDate.date()

    start_date_weekend = new_start_date.weekday()
    if start_date_weekend > 4:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be during the weekend.")

    end_date_weekend = new_end_date.weekday()
    if end_date_weekend > 4:
        raise HTTPException(status_code=400, detail="Sprint end date cannot be during the weekend.")

    if new_start_date < current_date:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be earlier than today.")

    if new_end_date <= new_start_date:
        raise HTTPException(status_code=400, detail="Sprint end date cannot be earlier or equal to its start date.")

    all_sprints = crud.get_all_sprints(db, projectId=db_sprint.projectId)
    for current_sprint in all_sprints:
        if current_sprint.id != db_sprint.id:
            if new_start_date <= current_sprint.startDate.date() <= new_end_date or new_start_date <= current_sprint.endDate.date() <= new_end_date:
                raise HTTPException(status_code=400, detail="Given sprint dates overlap with dates of an already existing sprint.")

    return crud.update_sprint(db=db, sprint=sprint, db_sprint=db_sprint)

# ********************** STORIES ********************** #

#get all stories in project
@app.get("/stories/{project_id}", response_model=List[schemas.Story], tags=["Stories"])
async def read_all_stories_in_project(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):

    # get all stories in project
    db_stories = crud.get_all_stories_in_project(db, project_id, skip=skip, limit=limit)

    #for each story, get all tasks
    for story in db_stories:
        #get all tasks for story
        db_tasks = crud.get_all_story_tasks(db, storyId=story.id)

        #if there are no tasks, continue to next story
        if db_tasks is None or len(db_tasks) == 0:
            continue

        #check if all tasks are done and if so, set story to done
        allDone = True
        for task in db_tasks:
            if not task.isDone:
                allDone = False
                break

        #if all tasks are done, the story is done so need to commit it to db
        if allDone:
            story.isDone = True
            crud.update_story_isDone(db, story=story, story_id=story.id)

    #after checking all tasks in all stories in project, return all stories with fixed isDone

    return crud.get_all_stories_in_project(db, project_id, skip=skip, limit=limit)

# get story by id
@app.get("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def read_story(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #check the tasks of story 
    db_tasks = crud.get_all_story_tasks(db, storyId=id)
    #print(db_tasks)

    if db_tasks is None or len(db_tasks) == 0:
        print("no tasks")
        return db_story
    
    #goes through all tasks and if one is not done, the story is not done
    allDone = True
    for task in db_tasks:
        if not task.isDone:
            allDone = False
            break

    #if all tasks are done, the story is done so need to commit it to db
    if allDone:
        db_story.isDone = True
        db_story = crud.update_story_isDone(db, story=db_story, story_id=id)

    #get updated story
    return crud.get_story_by_id(db, story_id=id)

#create story
@app.post("/story", response_model=schemas.Story, tags=["Stories"])
async def create_story(story: schemas.StoryCreate, tests: List[schemas.AcceptenceTestCreate], db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    # check if user is part of the project
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_roles = crud.get_all_user_roles(db=db, projectId=story.projectId, userId=db_user_data.id)

    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    
    # check if user is product owner or scrum master
    is_user_project_owner_or_scrum_master = False
    for db_user_project_role in db_user_project_roles:
        if db_user_project_role.roleId == 1 or db_user_project_role.roleId == 2:
            is_user_project_owner_or_scrum_master = True
            break
    
    if not is_user_project_owner_or_scrum_master:
        raise HTTPException(status_code=400, detail="Currently logged user must be product owner or scrum master at this project, in order to perform this action.")

    # check if story with same name already exists
    # check for lower case and TODO spaces? 
    all_stories_in_project = crud.get_all_stories_in_project(db, projectId=story.projectId)
    for story_in_proj in all_stories_in_project:
        if story_in_proj.name.lower() == story.name.lower() and story_in_proj.id != id:
            raise HTTPException(status_code=400, detail="Story with given name already exists in this project")
    
    # db_story = crud.get_story_by_name(db, name=story.name)
    # if db_story:
    #     raise HTTPException(status_code=400, detail="Story already exists")

    #check that priority is one of the allowed values
    if story.priority not in ["Must have", "Should have", "Could have","Won't have at this time"]:
        raise HTTPException(status_code=400, detail="Priority must be one of the following: Must have, Should have, Could have, Won't have at this time.")
    
    # check if project with given id exists
    db_project = crud.get_project_by_id(db=db, identifier=story.projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    # check if there is any tests
    if tests is None:
        raise HTTPException(status_code=400, detail="Acceptence tests cannot be empty.")
    
    #check if time estiamte is not 0 or none
    if story.timeEstimate > 0 and story.timeEstimate is not None: 
        story.timeEstimateOriginal = story.timeEstimate
    
    # create the story
    new_story = crud.create_story(db=db, story=story)

    # create and add tests to story
    for test in tests:
        if test.description is None:
            raise HTTPException(status_code=400, detail="Acceptence test description cannot be empty.")
        
        test = crud.create_test(db=db, test=test, story_id=new_story.id)
    
    return new_story

#update story
@app.put("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def update_story(id: int, story: schemas.Story, tests: List[schemas.AcceptenceTestCreate], db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # All tests providet will be added to the story thus only new tests should be given to the function in tests parameter. 
    # Old tests are already included in story object and MUST NOT be given to the function in tests parameter.
    # SprintID CANNOT be changed here as story cant be aprt of a sprint in order to be updated. Change sprintID in sprint endpoint.

    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    #user data from token
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)

    # check if user is part of the project
    db_user_project_roles = crud.get_all_user_roles(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    
    # check if user is product owner or scrum master
    is_user_project_owner_or_scrum_master = False
    for role in db_user_project_roles:
        if role.roleId == 1 or role.roleId == 2:
            is_user_project_owner_or_scrum_master = True
            break
    if not is_user_project_owner_or_scrum_master:
        raise HTTPException(status_code=400, detail="Currently logged user must be product owner or scrum master at this project, in order to perform this action.")
    
    # check that story is not in sprint
    if db_story.sprint_id is not None:
        raise HTTPException(status_code=400, detail="Story already assigned to a sprint cannot be updated.")
    
    #check that story is not done
    if db_story.isDone:
        raise HTTPException(status_code=400, detail="Finished story cannot be updated.")

    # check that name is not duplicate
    # check for capital letters TODO and spaces? 
    all_stories_in_project = crud.get_all_stories_in_project(db, projectId=story.projectId)
    for story_in_proj in all_stories_in_project:
        if story_in_proj.name.lower() == story.name.lower() and story_in_proj.id != id:
            raise HTTPException(status_code=400, detail="Story with given name already exists in this project")
    
    # check that name is not empty string or "string" use old name if it is
    if story.name == "" or story.name == "string":
        story.name = db_story.name
    
    # check that description is not empty string or "string" use old description if it is
    if story.storyDescription == "string" or story.storyDescription == "" or story.storyDescription is None:
        story.storyDescription = db_story.storyDescription

    # check for priority must be one of the following: "Must have", "Should have", "Could have", "Won't have at this time"
    if story.priority != "Must have" and story.priority != "Should have" and story.priority != "Could have" and story.priority != "Won't have at this time":
        raise HTTPException(status_code=400, detail="Priority must be one of the following: 'Must have', 'Should have', 'Could have', 'Won't have at this time'.")
    
    # check tha business value is within range 1-10
    if story.businessValue < 1 or story.businessValue > 10:
        raise HTTPException(status_code=400, detail="Business value must be in range 1-10.")
    
    # create any new acceptence tests
    for test in tests:
        if test.description is None or test.description == "":
            raise HTTPException(status_code=400, detail="Acceptence test description cannot be empty.")
    
        test = crud.create_test(db=db, test=test, story_id=story.id)
    
    # update the story

    #update the acceptence tests
    #check if tests in story have empty description
    for test in story.acceptenceTests:
        if test.description is None or test.description == "":
            raise HTTPException(status_code=400, detail="Acceptence test description cannot be empty.")

    # get all tests in database for story
    db_tests = crud.get_all_tests_in_story(db=db, story_id=id)
    #update the test 
    for db_test in db_tests:
        # update test in database if it is in story object
        for test in story.acceptenceTests:
            if test.id == db_test.id:
                #update the test
                test = crud.update_test(db=db, test=test, test_id=test.id)
                break
    
    # update the time estimate
    db_story.timeEstimate = story.timeEstimate

    # if timeEstimateOriginal is NONE, set it to the same value as timeEstimate
    if db_story.timeEstimateOriginal is None or db_story.timeEstimateOriginal == 0:
        db_story.timeEstimateOriginal = db_story.timeEstimate

    # prevent changing projectId
    story.projectId = db_story.projectId

    # prevent completion of story
    story.isDone = db_story.isDone

    #prevent changing original time estimate
    story.timeEstimateOriginal = db_story.timeEstimateOriginal

    # prevent changing sprint id
    story.sprint_id = db_story.sprint_id

    # update story
    return crud.update_story_generic(db=db, story=story, story_id=id)

# update only sprint id of story
@app.put("/story/{id}/sprint", response_model=schemas.Story, tags=["Stories"])
async def update_story_sprint(id: int, story: schemas.Story, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # only the sprint id can be changed with this function
    
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #get user data
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    # check if user is part of the project
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    # check if user is scrum master
    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    # check that story is not done
    if db_story.isDone:
        raise HTTPException(status_code=400, detail="Finished story cannot be assigned to a sprint.")
    
    # check that story is not already in sprint
    if db_story.sprint_id is not None:
        raise HTTPException(status_code=400, detail="Story already assigned to a sprint.")
    
    # check that story has non-zero time estimate
    if db_story.timeEstimate == 0 or db_story.timeEstimate is None:
        raise HTTPException(status_code=400, detail="Story with zero or no time estimate cannot be assigned to a sprint.")
    
    if story.sprint_id is None:
        raise HTTPException(status_code=400, detail="Select a sprint to assign the story to.")
    
    #check that story and sprint are in the same project
    db_sprint = crud.get_sprint_by_id(db, sprintId=story.sprint_id)
    if db_story.projectId != db_sprint.projectId:
        raise HTTPException(status_code=400, detail="Story and sprint must be in the same project.")

    # check that sprint with given id exists
    db_sprint = crud.get_sprint_by_id(db, sprintId=story.sprint_id)
    if db_sprint is None:
        raise HTTPException(status_code=404, detail="Sprint does not exist")
    
    #check that sprint velocity will not be exceeded
    #get all stories in sprint
    vsota_te_in_sprint = 0
    db_sprint_stories = crud.get_all_stories_in_sprint(db=db, sprintId=story.sprint_id)

    #calculate sum of time estimates of stories in sprint
    for story in db_sprint_stories:
        if story.timeEstimate is not None:
            vsota_te_in_sprint += story.timeEstimate

    #check if adding story to sprint would exceed sprint velocity
    if vsota_te_in_sprint + db_story.timeEstimate > db_sprint.velocity:
        raise HTTPException(status_code=400, detail="Sprint velocity would be exceeded.")
    
    return crud.update_story_sprint_id(db=db, new_sprint_id=story.sprint_id, story_id=id)

# update only timeEstiamte of story
@app.put("/story/{id}/timeEstimate", response_model=schemas.Story, tags=["Stories"])
async def update_story_timeEstimate(id: int, story_time: schemas.Story, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    
    # check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")

    #get user data 
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    # check if user is part of the project
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    # check if user is scrum master
    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    
    # prevent changing the time estiamte if story is already part of a sprint
    if db_story.sprint_id is not None:
        raise HTTPException(status_code=400, detail="Story that is already part of a sprint cannot be given a new time estimate.")
    
    # update the time estimate
    db_story.timeEstimate = story_time.timeEstimate

    # if timeEstimateOriginal is NONE, set it to the same value as timeEstimate
    if db_story.timeEstimateOriginal is None:
        db_story.timeEstimateOriginal = story_time.timeEstimate

    return crud.update_story_time_estimate(db=db, story=db_story, story_id=id)

#delete za story
@app.delete("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def delete_story(id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #get user data
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_roles = crud.get_all_user_roles(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    #check if user is part of the project
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    
    #check if user is Scrum Master or Product Owner
    is_user_sm_po = False
    for role in db_user_project_roles:
        if role.roleId == 2 or role.roleId == 1:
            is_user_sm_po = True
            break
    if not is_user_sm_po:
        raise HTTPException(status_code=400, detail="Currently logged user is not Scrum Master or Product Owner.")
    
    #check if story is part of a sprint
    if db_story.sprint_id is not None:
        raise HTTPException(status_code=400, detail="Can't delete story that is part of a sprint.")
    
    #check if story has tasks
    db_story_tasks = crud.get_all_story_tasks(db=db, storyId=id)
    if db_story_tasks:
        #check if tasks have any time logged
        for task in db_story_tasks:
            db_task_time = crud.check_any_time_logged(db=db, taskId=task.id)
            if db_task_time:
                raise HTTPException(status_code=400, detail="Can't delete story that has tasks with time logged.")

    #check that story is not done
    if db_story.isDone:
        raise HTTPException(status_code=400, detail="Can't delete story that is done.")
    
    # delete acceptanse tests for story
    db_story_tests = crud.get_all_tests_in_story(db=db, story_id=id)
    for test in db_story_tests:
        crud.delete_test(db=db, testId=test.id)
    
    return crud.delete_story(db=db, story_id=id)

# reject story for sprint
@app.post("/story/{id}/reject", response_model=schemas.Story, tags=["Stories"])
async def reject_story(id: int,  story: schemas.Story, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    #Changes sprint_id to None and updates the reject reason.

    # check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #get user data
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    # check if user is part of the project
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    # check if user is PO
    if db_user_project_role.roleId != 1:
        raise HTTPException(status_code=400, detail="Currently logged user must be product owner for this project, in order to perform this action.")

    #check if story is part of a sprint
    if db_story.sprint_id is None:
        raise HTTPException(status_code=400, detail="Can't reject story that is not part of a sprint.")
    
    #check that sprint is active and not done
    db_sprint = crud.get_sprint_by_id(db=db, sprintId=db_story.sprint_id)
    
    if db_sprint.endDate.date() < datetime.date.today():
        raise HTTPException(status_code=400, detail="Can't reject story that is part of a done sprint.")
    
    if db_sprint.startDate.date() > datetime.date.today():
        raise HTTPException(status_code=400, detail="Can't reject story that is part of a sprint that is not active.")
    
    #check if story is confiremd
    if db_story.isConfirmed:
        raise HTTPException(status_code=400, detail="Can't reject story that has already been confirmed.")
    
    #reject story 
    return crud.reject_story_from_sprint(db=db, story=story)


# accept story for sprint
@app.post("/story/{id}/accept", response_model=schemas.Story, tags=["Stories"])
async def accept_story(id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    #Changes sprint_id to None and updates isConfirmed to true.

    # check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #get user data
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    # check if user is part of the project
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    # check if user is PO
    if db_user_project_role.roleId != 1:
        raise HTTPException(status_code=400, detail="Currently logged user must be product owner for this project, in order to perform this action.")

    #check if story is part of a sprint
    if db_story.sprint_id is None:
        raise HTTPException(status_code=400, detail="Can't reject story that is not part of a sprint.")
    
    #check that sprint is active and not done
    db_sprint = crud.get_sprint_by_id(db=db, sprintId=db_story.sprint_id)
    
    if db_sprint.endDate.date() < datetime.date.today():
        raise HTTPException(status_code=400, detail="Can't reject story that is part of a done sprint.")
    
    if db_sprint.startDate.date() > datetime.date.today():
        raise HTTPException(status_code=400, detail="Can't reject story that is part of a sprint that is not yet active.")
    
    #check if story isDone
    if not db_story.isDone:
        raise HTTPException(status_code=400, detail="Can't accept story that has unfinished tasks.")
    
    #check if story is confiremd
    if db_story.isConfirmed:
        raise HTTPException(status_code=400, detail="Can't accpet story that has already been confirmed.")
    
    #accept story
    return crud.accept_story_in_sprint(db=db, story_id=id)



@app.get("/task/{storyId}/all", response_model=List[schemas.TaskWithRemainingEstimate], tags=["Tasks"])
async def list_all_story_tasks(storyId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db=db, story_id=storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with given identifier does not exist.")

    db_tasks = crud.get_all_story_tasks(db, storyId=storyId, skip=skip, limit=limit)

    response = []
    for task in db_tasks:
        time_remaining = None
        if task.isDone:
            time_remaining = 0
        else:
            db_worklogs = crud.list_timelogs_by_task_id(db=db, taskId=task.id)
            if db_worklogs and db_worklogs[0]:
                time_remaining = db_worklogs[0].timeRemainingEstimate
            else:
                time_remaining = task.timeEstimate
        response.append(schemas.TaskWithRemainingEstimate(id=task.id, name=task.name, description=task.description, timeEstimate=task.timeEstimate, assigneeUserId=task.assigneeUserId, hasAssigneeConfirmed=task.hasAssigneeConfirmed, isActive=task.isActive, isDone=task.isDone, storyId=task.storyId, timeRemainingEstimate=time_remaining))

    return response

@app.get("/task/{sprintId}/{userId}/all", response_model=List[schemas.TaskWithRemainingEstimate], tags=["Tasks"])
async def all_sprint_user_accepted_tasks(sprintId: int, userId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_sprint = crud.get_sprint_by_id(db=db, sprintId=sprintId)
    if not db_sprint:
        raise HTTPException(status_code=400, detail="Sprint with given identifier does not exist.")
    db_user = crud.get_user_by_id(db=db, identifier=userId)
    if not db_user:
        raise HTTPException(status_code=400, detail="User with given identifier does not exist.")
    if db_sprint.projectId is None:
        raise HTTPException(status_code=400, detail="Sprint is not part of any project.")
    db_project = crud.get_project_by_id(db=db, identifier=db_sprint.projectId)
    if db_project is None:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    db_stories = crud.get_all_stories_in_project(db=db, projectId=db_project.id)

    response = []
    for story in db_stories:
        db_tasks = crud.get_all_story_user_tasks(db, storyId=story.id, userId=db_user.id, skip=skip, limit=limit)
        for task in db_tasks:
            time_remaining = None
            if task.isDone:
                time_remaining = 0
            else:
                db_worklogs = crud.list_timelogs_by_task_id(db=db, taskId=task.id)
                if db_worklogs and db_worklogs[0]:
                    time_remaining = db_worklogs[0].timeRemainingEstimate
                else:
                    time_remaining = task.timeEstimate
            response.append(schemas.TaskWithRemainingEstimate(id=task.id, name=task.name, description=task.description, timeEstimate=task.timeEstimate, assigneeUserId=task.assigneeUserId, hasAssigneeConfirmed=task.hasAssigneeConfirmed, isActive=task.isActive, isDone=task.isDone, storyId=task.storyId, timeRemainingEstimate=time_remaining))

    return response


@app.get("/task/{taskId}", response_model=schemas.TaskWithRemainingEstimate, tags=["Tasks"])
async def get_task(taskId: int, db: Session = Depends(get_db)):
    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    time_remaining = None
    if db_task.isDone:
        time_remaining = 0
    else:
        db_worklogs = crud.list_timelogs_by_task_id(db=db, taskId=taskId)
        if db_worklogs and db_worklogs[0]:
            time_remaining = db_worklogs[0].timeRemainingEstimate
        else:
            time_remaining = db_task.timeEstimate

    return schemas.TaskWithRemainingEstimate(id=db_task.id, name=db_task.name, description=db_task.description, timeEstimate=db_task.timeEstimate, assigneeUserId=db_task.assigneeUserId, hasAssigneeConfirmed=db_task.hasAssigneeConfirmed, isActive=db_task.isActive, isDone=db_task.isDone, storyId=db_task.storyId, timeRemainingEstimate=time_remaining)


@app.post("/task/{storyId}", response_model=schemas.Task, tags=["Tasks"])
async def create_task(storyId: int, task: schemas.TaskInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Mandatory fields should be checked by frontend (check if mandatory ones are fulfilled).

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_story = crud.get_story_by_id(db=db, story_id=storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId == 1:
        raise HTTPException(status_code=400, detail="Product owner cannot perform this action.")

    if db_story.isDone:
        raise HTTPException(status_code=400, detail="Cannot add new task under story that has already been marked as done.")

    db_sprint = crud.get_sprint_by_id(db=db, sprintId=db_story.sprint_id)
    if not db_sprint:
        raise HTTPException(status_code=400, detail="Cannot add new task under story that isn't connected to any sprint.")

    current_date = datetime.date.today()
    if not db_sprint.startDate.date() <= current_date <= db_sprint.endDate.date():
        raise HTTPException(status_code=400, detail="Cannot add new task under story of currently not active sprint.")

    db_story_tasks = crud.get_all_story_tasks(db=db, storyId=storyId)
    for current_task in db_story_tasks:
        if current_task.name.lower() == task.name.lower():
            raise HTTPException(status_code=400, detail="Task with identical name already exist under this story.")

    if task.timeEstimate <= 0:
        raise HTTPException(status_code=400, detail=f"Time estimate must be a positive number.")

    if task.assigneeUserId is not None:
        db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=task.assigneeUserId)
        if not db_user_project_role:
            raise HTTPException(status_code=400, detail="Selected assignee is not part of the selected project.")
        if db_user_project_role.roleId != 3:
            raise HTTPException(status_code=400, detail="Product owner and scrum master (without developer role) cannot be declared as task assignees.")

    return crud.create_task(db=db, task=task, storyId=storyId)


@app.put("/task/{taskId}/accept", response_model=schemas.Task, tags=["Tasks"])
async def accept_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Product owner and scrum master (without developer role) cannot accept tasks.")

    if db_task.assigneeUserId is not None:
        if db_user_data.id != db_task.assigneeUserId:
            raise HTTPException(status_code=400, detail="Selected task is already assigned to other user.")
        if db_user_data.id == db_task.assigneeUserId and db_task.hasAssigneeConfirmed:
            raise HTTPException(status_code=400, detail="This task is already assigned to you, no action required.")
    if db_task.isDone:
        raise HTTPException(status_code=400, detail="Already done tasks cannot be accepted again.")

    return crud.update_task_assignee_confirm(db=db, taskId=taskId, userId=db_user_data.id)


@app.put("/task/{taskId}/decline", response_model=schemas.Task, tags=["Tasks"])
async def decline_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Product owner and scrum master (without developer role) cannot decline tasks.")

    if db_task.assigneeUserId is None:
        raise HTTPException(status_code=400, detail="Unassigned tasks cannot be declined.")
    else:
        if db_user_data.id != db_task.assigneeUserId:
            raise HTTPException(status_code=400, detail="Task is assigned to somebody else, so you cannot decline it.")

    return crud.update_task_assignee_decline(db=db, taskId=taskId)


@app.put("/task/{taskId}/done", response_model=schemas.Task, tags=["Tasks"])
async def done_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Product owner and scrum master (without developer role) cannot mark tasks as done.")

    if db_task.assigneeUserId is None:
        raise HTTPException(status_code=400, detail="Unassigned tasks cannot be marked as done.")
    if db_user_data.id != db_task.assigneeUserId:
        raise HTTPException(status_code=400, detail="Task is assigned to somebody else, so you cannot mark it as done.")
    if not db_task.hasAssigneeConfirmed:
        raise HTTPException(status_code=400, detail="Task cannot be marked as done until you confirm it.")
    if db_task.isDone:
        raise HTTPException(status_code=400, detail="This task has already been marked as done.")

    if not crud.check_any_time_logged(db=db, taskId=taskId):
        raise HTTPException(status_code=400, detail="There must be at least some work logged, in order to mark task as done.")

    return crud.update_task_assignee_done(db=db, taskId=taskId)


@app.put("/task/{taskId}", response_model=schemas.Task, tags=["Tasks"])
async def update_task(taskId: int, task: schemas.TaskInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId == 1:
        raise HTTPException(status_code=400, detail="Product owner cannot edit tasks.")

    if db_task.isDone:
        raise HTTPException(status_code=400, detail="Tasks that are marked as done cannot be edited.")

    if db_task.assigneeUserId is not None:
        raise HTTPException(status_code=400, detail="Already assigned tasks cannot be edited.")

    db_story_tasks = crud.get_all_story_tasks(db=db, storyId=db_story.id)
    for current_task in db_story_tasks:
        if current_task.name.lower() == task.name.lower():
            if db_task.name != task.name:
                raise HTTPException(status_code=400, detail="Task with identical name already exist under this story.")

    if task.timeEstimate <= 0:
        raise HTTPException(status_code=400, detail=f"Time estimate must be a positive number.")

    if task.assigneeUserId is not None:
        db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=task.assigneeUserId)
        if not db_user_project_role:
            raise HTTPException(status_code=400, detail="Selected assignee is not part of the selected project.")
        if db_user_project_role.roleId != 3:
            raise HTTPException(status_code=400, detail="Product owner and scrum master (without developer role) cannot be declared as task assignees.")

    return crud.update_task(db=db, task=task, db_task=db_task)


@app.delete("/task/{taskId}", response_model=schemas.Task, tags=["Tasks"])
async def delete_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId == 1:
        raise HTTPException(status_code=400, detail="Product owner cannot delete tasks.")

    if db_task.isDone:
        raise HTTPException(status_code=400, detail="Tasks that are marked as done cannot be deleted.")

    if db_task.hasAssigneeConfirmed:
        raise HTTPException(status_code=400, detail="Accepted tasks cannot be deleted.")

    if crud.check_any_time_logged(db=db, taskId=taskId):
        raise HTTPException(status_code=400, detail="Task cannot be deleted if it has any logged work.")

    return crud.delete_task(db=db, taskId=taskId)


@app.get("/messages/{projectId}/all", response_model=List[schemas.Message], tags=["Messages"])
async def list_all_project_messages(projectId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")
    return crud.get_all_project_messages(db, projectId=projectId, skip=skip, limit=limit)


@app.get("/messages/{projectId}/my", response_model=List[schemas.Message], tags=["Messages"])
async def list_my_project_messages(projectId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    return crud.get_my_project_messages(db, projectId=projectId, userId=db_user_data.id, skip=skip, limit=limit)


@app.post("/messages/{projectId}", response_model=schemas.Message, tags=["Messages"])
async def create_message(projectId: int, message: schemas.MessageInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if len(message.content) == 0:
        raise HTTPException(status_code=400, detail="Message must not be empty.")

    return crud.create_message(db=db, message=message, userId=db_user_data.id, projectId=projectId)


@app.put("/project/documentation/{projectId}", tags=["Documentation"])
async def update_project_documentation(projectId: int, documentation: schemas.ProjectDocumentation, db: Session = Depends(get_db)):
    # Backend does not check which user is currently logged in, since there is no requirement for role checking here.
    # Therefore, backend does not check if user is part of the project, so frontend must take care of that.

    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    return crud.update_documentation(db=db, documentation=documentation, db_project=db_project)


@app.post("/project/documentation/export/{projectId}", tags=["Documentation"])
async def export_project_documentation(projectId: int, db: Session = Depends(get_db)):
    # Backend does not check which user is currently logged in, since there is no requirement for role checking here.
    # Therefore, backend does not check if user is part of the project, so frontend must take care of that.

    db_project = crud.get_project_by_id(db=db, identifier=projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    filename = f"project_{db_project.id}_documentation.txt"
    with open(filename, "w") as file:
        if db_project.documentation == "":
            file.write(" ")
        else:
            file.write(db_project.documentation)

    return FileResponse(filename, media_type="text/plain", filename=filename)


@app.post("/project/documentation/import", tags=["Documentation"])
async def import_project_documentation(file: UploadFile = File(...)):
    # This endpoint is only meant for uploading documentation from text file to screen.
    # For uploading new documentation, you must use PUT endpoint.
    # For now, frontend must take care for handling overwriting (append text or overwrite text).

    text = await file.read()
    text_data = text.decode()
    return text_data


@app.put("/task/start/{taskId}", response_model=schemas.Task, tags=["Tasks - Work time"])
async def start_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Only developers can start working on tasks.")

    if db_task.isDone:
        raise HTTPException(status_code=400, detail="This task is already finished (marked as done).")

    if db_task.isActive:
        raise HTTPException(status_code=400, detail="This task has already been started.")

    if db_task.assigneeUserId != db_user_data.id:
        raise HTTPException(status_code=400, detail="This task is assigned to other user.")

    if not db_task.hasAssigneeConfirmed:
        raise HTTPException(status_code=400, detail="You have to confirm the task first until you start making progress.")

    my_tasks = crud.get_all_my_tasks(db=db, userId=db_user_data.id)
    for task in my_tasks:
        if task.id != taskId:
            if task.isActive:
                raise HTTPException(status_code=400, detail="You already have at least one task in progress right now. You can only work on one task at a time.")

    crud.insert_work_progress(db=db, taskId=taskId)

    return crud.set_active_task(db=db, db_task=db_task)


@app.put("/task/stop/{taskId}", response_model=schemas.WorkTime, tags=["Tasks - Work time"])
async def stop_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Automatically marks task as done and marks as inactive (same thing as endpoint for doing this explicitly), if remaining estimate is calculated to be 0.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Only developers can stop working on tasks.")

    if db_task.isDone:
        raise HTTPException(status_code=400, detail="This task is already finished (marked as done).")

    if not db_task.isActive:
        raise HTTPException(status_code=400, detail="This task hasn't been started yet, so it cannot be stopped.")

    if db_task.assigneeUserId != db_user_data.id:
        raise HTTPException(status_code=400, detail="This task is assigned to other user.")

    if not db_task.hasAssigneeConfirmed:
        raise HTTPException(status_code=400, detail="You have to confirm the task first until you stop making progress.")

    _ = crud.set_inactive_task(db=db, db_task=db_task)
    work_done = crud.get_work_progress(db=db, taskId=taskId)

    response = crud.update_worktime(db=db, taskId=taskId, taskEstimate=db_task.timeEstimate, userId=db_user_data.id, workDone=work_done)

    if response.timeRemainingEstimate == 0:
        _ = crud.update_task_assignee_done(db=db, taskId=taskId)

    return response


@app.put("/task/worktime/{taskId}", response_model=schemas.WorkTime, tags=["Tasks - Work time"])
async def worktime_task(taskId: int, workTime: schemas.WorkTimeInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Automatically recognizes whether the worklog has to be added under new date or updated under existing date.
    # Automatically marks task as done and marks as inactive (same thing as endpoint for doing this explicitly), if remaining estimate is put to 0.
    # We assume that frontend serves valid date if it is the first entry.
    # Backend doesn't check if the date is in valid range (ordered), it just recognizes whether to update worklog entry or add a new one.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    if db_user_project_role.roleId != 3:
        raise HTTPException(status_code=400, detail="Only developers can log time on tasks.")

    if db_task.isDone:
        raise HTTPException(status_code=400, detail="This task is already finished (marked as done).")

    if db_task.assigneeUserId != db_user_data.id:
        raise HTTPException(status_code=400, detail="This task is assigned to other user.")

    if not db_task.hasAssigneeConfirmed:
        raise HTTPException(status_code=400, detail="You have to confirm the task first until you can log time.")

    if workTime.timeDone <= 0:
        raise HTTPException(status_code=400, detail="Work time must be a positive number.")

    if workTime.timeRemainingEstimate < 0:
        raise HTTPException(status_code=400, detail="Remaining estimate time must be > 0.")

    response = crud.update_or_insert_worktime(db=db, taskId=taskId, userId=db_user_data.id, workTime=workTime)

    if workTime.timeRemainingEstimate == 0:
        _ = crud.update_task_assignee_done(db=db, taskId=taskId)

    return response


@app.get("/task/worktime/all/{taskId}", response_model=List[schemas.WorkTime], tags=["Tasks - Work time"])
async def list_worktime_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Shows all worklog entries of selected task.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    return crud.list_timelogs_by_task_id(db=db, taskId=taskId)


@app.get("/task/worktime/my/{taskId}", response_model=List[schemas.WorkTime], tags=["Tasks - Work time"])
async def list_my_worktime_task(taskId: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Only shows worklog entries for currently logged user.

    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")

    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")

    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_story = crud.get_story_by_id(db=db, story_id=db_task.storyId)

    if not db_story:
        raise HTTPException(status_code=400, detail="Story with identifier, stated in selected task, does not exist.")

    db_user_project_role = crud.get_user_role_from_project_descending(db=db, projectId=db_story.projectId, userId=db_user_data.id)

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")

    return crud.list_timelogs_by_task_id_by_user_id(db=db, taskId=taskId, userId=db_user_data.id)
