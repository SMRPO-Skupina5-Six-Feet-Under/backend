from fastapi import status
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request
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
    userTryingToLogIn: schemas.UserBase = crud.get_UporabnikBase_by_username(db, logInData.userName)
    if userTryingToLogIn is not None and userTryingToLogIn.userName == logInData.userName and userTryingToLogIn.password == logInData.password:
        access_token = Authorize.create_access_token(subject=userTryingToLogIn.userName)
        __returnUser = copy.deepcopy(userTryingToLogIn)
        crud.setUserLogInTime(db, userTryingToLogIn.id)
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
    user_name: str = Authorize.get_jwt_subject()  # get username from logged in user - trough Authentication Header
    user_to_change: schemas.UserBase = crud.get_user_by_id(db, userId)
    if user_to_change is None:
        raise HTTPException(status_code=404, detail="User with this id is not present in database.")
    if user_to_change.userName != user_name:
        raise HTTPException(status_code=400, detail="Id and username missmatch")
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


@app.get("/project/all", response_model=List[schemas.Project], tags=["Projects"])
async def list_all_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_projects = crud.get_all_projects(db, skip=skip, limit=limit)

    response_data: List[schemas.Project] = []
    for project in db_projects:
        db_project_participants = crud.get_project_participants(db=db, projectId=project.id)
        project_data = schemas.Project(id=project.id, name=project.name, description=project.description, projectParticipants=db_project_participants)
        response_data.append(project_data)

    return response_data


@app.get("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def get_project(identifier: int, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    db_project_participants = crud.get_project_participants(db=db, projectId=identifier)
    response_project_data = schemas.Project(id=db_project.id, name=db_project.name, description=db_project.description, projectParticipants=db_project_participants)

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
        raise HTTPException(status_code=400, detail="Currently logged user must have admin rights, in order to perform this action.")

    db_project = crud.get_all_projects(db=db)
    for current_project in db_project:
        if current_project.name.lower() == project.name.lower():
            raise HTTPException(status_code=400, detail="Project with such name already exist.")

    check, message = static.check_project_roles(project.projectParticipants, db)
    if not check:
        raise HTTPException(status_code=400, detail=message)

    return crud.create_project(db=db, project=project)


@app.delete("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def delete_project(identifier: int, db: Session = Depends(get_db)):
    # We assume that frontend always serves only projects that actually exist.
    # Therefore, there is no need for additional check for project existence on backend.
    return crud.delete_project(db=db, identifier=identifier)


@app.get("/project/roles/", tags=["Projects"])
async def get_project_roles() -> list[schemas.ProjectRole]:
    return [
        schemas.ProjectRole(id=1, role="Product owner"),
        schemas.ProjectRole(id=2, role="Scrum master"),
        schemas.ProjectRole(id=3, role="Developer"),
    ]


@app.patch("/project/{identifier}/data", response_model=schemas.Project, tags=["Projects"])
async def update_project_data(identifier: int, project: schemas.ProjectDataPatch, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
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

    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project or is not system administrator.")

    if db_user_project_role.roleId != 2 or not db_user_data.isAdmin:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")

    if project.name is not None:
        db_project = crud.get_all_projects(db=db)
        for current_project in db_project:
            if current_project.name.lower() == project.name.lower():
                raise HTTPException(status_code=400, detail="Project with such name already exist.")

    return crud.update_project_data(db=db, project=project, identifier=identifier)


@app.put("/project/{identifier}/participants", response_model=schemas.Project, tags=["Projects"])
async def update_project_data(identifier: int, story: schemas.ProjectParticipantsInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    return 5


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

    if sprint.velocity > 20:
        raise HTTPException(status_code=400, detail="Sprint velocity exceeds reasonable range.")

    current_date = datetime.date.today()
    if sprint.startDate.date() < current_date:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be earlier than today.")

    if sprint.endDate.date() <= sprint.startDate.date():
        raise HTTPException(status_code=400, detail="Sprint end date cannot be earlier or equal to its start date.")

    all_sprints = crud.get_all_sprints(db, projectId=projectId)
    for current_sprint in all_sprints:
        if sprint.startDate.date() <= current_sprint.start.date() <= sprint.endDate.date() or sprint.startDate.date() <= current_sprint.endDate.date() <= sprint.endDate.date():
            raise HTTPException(status_code=400, detail="Given sprint dates overlap with dates of an already existing sprint.")

    return crud.create_sprint(db=db, sprint=sprint, projectId=projectId)


@app.get("/stories/{project_id}", response_model=List[schemas.Story], tags=["Stories"])
async def read_all_stories_in_project(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_stories_in_project(db, project_id, skip=skip, limit=limit)


@app.get("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def read_story(identifier: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=identifier)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return db_story


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
    if not db_user_project_roles:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    
    # check if user is product owner or scrum master
    for db_user_project_role in db_user_project_roles:
        if db_user_project_role.roleId == 1 or db_user_project_role.roleId == 2:
            is_user_project_owner_or_scrum_master = True
            break
    
    if not is_user_project_owner_or_scrum_master:
        raise HTTPException(status_code=400, detail="Currently logged user must be product owner or scrum master at this project, in order to perform this action.")

    # check if story with same name already exists
    db_story = crud.get_story_by_name(db, name=story.name)
    if db_story :
        raise HTTPException(status_code=400, detail="Story already exists")
    
    # check if project with given id exists
    db_project = crud.get_project_by_id(db=db, identifier=story.projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    # check if there is any tests
    if tests is None:
        raise HTTPException(status_code=400, detail="Acceptence tests cannot be empty.")
    
    # create the story
    new_story = crud.create_story(db=db, story=story)

    # create and add tests to story
    for test in tests:
        if test.description is None:
            raise HTTPException(status_code=400, detail="Acceptence test description cannot be empty.")
        
        test = crud.create_test(db=db, test=test, story_id=new_story.id)
    
    return new_story


@app.put("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def update_story(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    # check that name is not duplicate
    #TODO check for capital letters and spaces
    db_story_same_name = crud.get_story_by_name(db, name=story.name)
    if db_story_same_name is not None and db_story_same_name.id != id:
        raise HTTPException(status_code=400, detail="Story with given name already exists")
    
    # check that name is not empty string or "string"
    if story.name == "" or story.name == "string":
        story.name = db_story.name
    
    # check that description is not empty string or "string"
    if story.storyDescription == "string":
        story.storyDescription = db_story.storyDescription

    # check that priority is not "string"
    if story.priority == "string":
        story.priority = db_story.priority
    
    # check that sprint exists 
    db_sprint = crud.get_sprint_by_id(db, sprintId=story.sprint_id)
    if db_sprint is None:
        raise HTTPException(status_code=404, detail="Sprint does not exist")

    # prevent changing projectId
    story.projectId = db_story.projectId

    # check for priority must be one of the following: "Must have", "Should have", "Could have", "Won't have this time"
    if story.priority != "Must have" and story.priority != "Should have" and story.priority != "Could have" and story.priority != "Won't have this time":
        raise HTTPException(status_code=400, detail="Priority must be one of the following: 'Must have', 'Should have', 'Could have', 'Won't have this time'.")
    
    return crud.update_story_generic(db=db, story=story, story_id=id)


# update only sprint id of story
@app.put("/story/{id}/sprint", response_model=schemas.Story, tags=["Stories"])
async def update_story_sprint(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    # check that sprint with given id exists
    db_sprint = crud.get_sprint_by_id(db, sprintId=story.sprint_id)
    if db_sprint is None:
        raise HTTPException(status_code=404, detail="Sprint does not exist")

    return crud.update_story_sprint_id(db=db, new_sprint_id=story.sprint_id, story_id=id)


# update only isDone and endDate of story
@app.put("/story/{id}/isDone", response_model=schemas.Story, tags=["Stories"])
async def update_story_isDone(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):
    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
   
    # prevent changing anything else
    story.sprint_id = None
    story.projectId = None
    story.name = None
    story.storyDescription = None

    return crud.update_story_isDone(db=db, story=story, story_id=id)


@app.delete("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def delete_story(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return crud.delete_story(db=db, story_id=id)


@app.get("/task/{storyId}/all", response_model=List[schemas.Task], tags=["Tasks"])
async def list_all_story_tasks(storyId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db=db, story_id=storyId)
    if not db_story:
        raise HTTPException(status_code=400, detail="Story with given identifier does not exist.")
    return crud.get_all_story_tasks(db, storyId=storyId, skip=skip, limit=limit)


@app.get("/task/{taskId}", response_model=schemas.Task, tags=["Tasks"])
async def get_task(taskId: int, db: Session = Depends(get_db)):
    db_task = crud.get_task_by_id(db=db, taskId=taskId)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task with given identifier does not exist.")
    return db_task


@app.post("/task/{storyId}", response_model=schemas.Task, tags=["Tasks"])
async def create_task(storyId: int, task: schemas.TaskInput, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # Mandatory fields should be checked by frontend (check if mandatory ones are fulfilled).
    # We assume that frontend serves only valid users, that are actually part of the project, and not product owner.

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
    sum_time_tasks = 0
    for current_task in db_story_tasks:
        sum_time_tasks += current_task.timeEstimate
        if current_task.name.lower() == task.name.lower():
            raise HTTPException(status_code=400, detail="Task with identical name already exist under this story.")

    upper_bound = db_story.timeEstimate - sum_time_tasks
    if not 0 < task.timeEstimate <= upper_bound:
        raise HTTPException(status_code=400, detail=f"Time estimate must be a positive number with calculated upper bound of {upper_bound}.")

    return crud.create_task(db=db, task=task, storyId=storyId)
