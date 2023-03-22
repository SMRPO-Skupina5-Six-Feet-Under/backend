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
        project_data = schemas.Project(name=project.name, id=project.id, projectParticipants=db_project_participants)
        response_data.append(project_data)

    return response_data


@app.get("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def get_project(identifier: int, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    db_project_participants = crud.get_project_participants(db=db, projectId=identifier)
    response_project_data = schemas.Project(name=db_project.name, id=db_project.id, projectParticipants=db_project_participants)

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

    db_project = crud.get_project_by_name(db=db, name=project.name)
    if db_project:
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

    current_date = datetime.date.today()
    if sprint.startDate < current_date:
        raise HTTPException(status_code=400, detail="Sprint start date cannot be earlier than today.")

    if sprint.endDate <= sprint.startDate:
        raise HTTPException(status_code=400, detail="Sprint end date cannot be earlier or equal to its start date.")

    all_sprints = crud.get_all_sprints(db, projectId=projectId)
    for current_sprint in all_sprints:
        if sprint.startDate <= current_sprint.startDate <= sprint.endDate or sprint.startDate <= current_sprint.endDate <= sprint.endDate:
            raise HTTPException(status_code=400, detail="Given sprint dates overlap with dates of an already existing sprint.")
    return crud.create_sprint(db=db, sprint=sprint, projectId=projectId)

# ============== ZGODBE ==============
#pridobi vse zgodbe v projektu z id-jem
@app.get("/stories/{project_id}", response_model=List[schemas.Story], tags=["Stories"])
async def read_all_stories_in_project(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_stories_in_project(db, project_id, skip=skip, limit=limit)

#pridobi eno zgodbo z id-jem
@app.get("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def read_story(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return db_story

#create story in project
@app.post("/story", response_model=schemas.Story, tags=["Stories"])
async def create_story(story: schemas.StoryCreate, tests: List[schemas.AcceptenceTestCreate] , db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):

    #check if user is logged in
    try:
        Authorize.jwt_required()
    except:
        raise HTTPException(status_code=403, detail="User not logged in, or the token expired. Please log in.")
    
    user_name = Authorize.get_jwt_subject()
    db_user_data = crud.get_UporabnikBase_by_username(db=db, userName=user_name)
    db_user_project_role = crud.get_user_role_from_project(db=db, projectId=story.projectId, userId=db_user_data.id)
    if not db_user_project_role:
        raise HTTPException(status_code=400, detail="Currently logged user is not part of the selected project.")
    if db_user_project_role.roleId != 2:
        raise HTTPException(status_code=400, detail="Currently logged user must be scrum master at this project, in order to perform this action.")


    #check if story with same name already exists
    db_story = crud.get_story_by_name(db, name=story.name)
    if db_story :
        raise HTTPException(status_code=400, detail="Story already exists")
    
    #check if project with given id exists
    db_project = crud.get_project_by_id(db=db, identifier=story.projectId)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")

    #check if there is any tests
    if tests is None:
        raise HTTPException(status_code=400, detail="Acceptence tests cannot be empty.")
    
    #create the story
    new_story = crud.create_story(db=db, story=story)

    #create and add tests to story
    for test in tests:
        if test.description is None:
            raise HTTPException(status_code=400, detail="Acceptence test description cannot be empty.")
        
        test = crud.create_test(db=db, test=test, story_id=new_story.id)
    
    return new_story

#update story
@app.put("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def update_story(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):

    # check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    # check that name is not duplicate
    db_story_same_name = crud.get_story_by_name(db, name=story.name)
    if db_story_same_name != None and db_story_same_name.id != id:
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
    
    # check that endDate is after startDate
    if db_story.startDate > story.endDate:
        raise HTTPException(status_code=400, detail="End date cannot be before start date.")

    # prevent changing projectId
    story.projectId = db_story.projectId

    # check for priority must be one of the following: "Must have", "Should have", "Could have", "Won't have this time"
    if story.priority != "Must have" and story.priority != "Should have" and story.priority != "Could have" and story.priority != "Won't have this time":
        raise HTTPException(status_code=400, detail="Priority must be one of the following: 'Must have', 'Should have', 'Could have', 'Won't have this time'.")
    
    return crud.update_story_generic(db=db, story=story, story_id=id)

#update only sprint id of story 
@app.put("/story/{id}/sprint", response_model=schemas.Story, tags=["Stories"])
async def update_story_sprint(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):
    
    #check if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #check that sprint with given id exists
    db_sprint = crud.get_sprint_by_id(db, sprintId=story.sprint_id)
    if db_sprint is None:
        raise HTTPException(status_code=404, detail="Sprint does not exist")

    return crud.update_story_sprint_id(db=db, new_sprint_id=story.sprint_id, story_id=id)

#update only isDone and endDate of story
@app.put("/story/{id}/isDone", response_model=schemas.Story, tags=["Stories"])
async def update_story_isDone(id: int, story: schemas.StoryUpdate, db: Session = Depends(get_db)):

    #chceck if story with given id exists
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    #check that endDate is after startDate
    if db_story.startDate > story.endDate:
        raise HTTPException(status_code=400, detail="End date cannot be before start date.")
    
    #prevent changing aynthing else
    story.sprint_id = None
    story.projectId = None
    story.name = None
    story.storyDescription = None
    story.startDate = None

    return crud.update_story_isDone(db=db, story=story, story_id=id)

#delete story
@app.delete("/story/{id}", response_model=schemas.Story, tags=["Stories"])
async def delete_story(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return crud.delete_story(db=db, story_id=id)