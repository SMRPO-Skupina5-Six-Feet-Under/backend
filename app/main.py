import datetime

from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI, status
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel
import copy

#za middleware
from fastapi.middleware.cors import CORSMiddleware

#local import files
from app import crud, models, schemas
from .schemas import UserBase, LogInData

app = FastAPI(
    title="SMRPOBackend",
    description="Backend za SMRPO projekt",
)

#"http://localhost",
#"http://localhost:4200",
#tu naj bi se napisalo url iz katerih je dovoljen dostop * naj bi bla za vse
#
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#init baze
#models.Base.metadata.drop_all(bind=engine) #če tega ni pol spremembe v classu (dodana polja) ne bojo v bazi
models.Base.metadata.create_all(bind=engine)





#------ CORE funkcionalnosti ------

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Hello najbolsa SMRPO ekipa :)"}

#-- LOGIN
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


@app.post('/login')
def login(logInData: schemas.LogInData, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):

    userTryingToLogIn: schemas.UserBase = crud.get_UporabnikBase_by_username(db, logInData.userName)
    if(userTryingToLogIn != None and userTryingToLogIn.userName == logInData.userName and userTryingToLogIn.password == logInData.password):
        access_token = Authorize.create_access_token(subject=userTryingToLogIn.userName)
        __returnUser = copy.deepcopy(userTryingToLogIn)
        crud.setUserLogInTime(db, userTryingToLogIn.id)
        return {"access_token": access_token, "user": __returnUser}
    else:
        raise HTTPException(status_code=401, detail='Incorrect username or password')


##-- end LOGIN


#-- USERS
@app.get("/users", response_model=List[schemas.UserBase])
async def get_all_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)

@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    userNameExists = crud.check_user_username_exist(db, user.userName)
    emailExists = crud.check_user_email_exist(db, user.email)
    if(userNameExists):
        raise HTTPException(status_code=400, detail="User with this username already exists.")
    elif(emailExists):
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    response = crud.create_user(db=db, user=user)
    return response
#-- end USERS


#request for 1 user data
@app.get('/uporabniki/{userName}', response_model=schemas.UserBase)
def user(userName: str, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return crud.get_UporabnikBase_by_username(db, userName)
    #return {"user": 123124124, 'data': 'jwt test works'}
    # current_user = Authorize.get_jwt_subject()
    # return {"user": current_user, 'data': 'jwt test works'}
#change pass
#@app.get('/users/{id}/change-pass', response_model=schemas.UserBase)
#def user(userName: str, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
#    Authorize.jwt_required()
#    current_user = get_jwt_identity()
#    print("krneki")
#    return crud.get_UporabnikBase_by_username(db, userName)
    #return {"user": 123124124, 'data': 'jwt test works'}
    # current_user = Authorize.get_jwt_subject()
    # return {"user": current_user, 'data': 'jwt test works'}

"""-----------EXAMPLES------------"""
#TODO 
#pridobi vse recepte v bazi
#@app.get("/projekti", response_model=List[schemas.Projekt])
#async def read_all_projekti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#    return crud.get_all_projekti(db, skip=skip, limit=limit)

#TODO
#testno naredi en projekt
#@app.post("/projekt", response_model=schemas.Projekt)
#async def create_kosarica(projekt: schemas.ProjektCreate, db: Session = Depends(get_db)):
    #db_projekt = crud.getProjektbyName(db, imeProjekta=projekt.imeProjekta)
    #print(db_projekt.imeProjekta)
    # if db_projekt:
    #     raise HTTPException(status_code=400, detail="Projekt ze obstaja")
#    return crud.create_projekt(db=db, projekt=projekt)