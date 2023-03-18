from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI, status
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import List

#za middleware
from fastapi.middleware.cors import CORSMiddleware

#local import files
from app import crud, models, schemas

app = FastAPI(
    title="SMRPOBackend",
    description="Backend za SMRPO projekt",
)

origins = [
    ""
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)


#init baze
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


#-------USERS-------
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