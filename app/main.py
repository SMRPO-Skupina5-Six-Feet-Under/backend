from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI
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

#TODO 
#pridobi vse recepte v bazi
@app.get("/projekti", response_model=List[schemas.Projekt])
async def read_all_projekti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_projekti(db, skip=skip, limit=limit)

#TODO
#testno naredi en projekt
@app.post("/projekt", response_model=schemas.Projekt)
async def create_kosarica(projekt: schemas.ProjektCreate, db: Session = Depends(get_db)):
    #db_projekt = crud.getProjektbyName(db, imeProjekta=projekt.imeProjekta)
    #print(db_projekt.imeProjekta)
    # if db_projekt:
    #     raise HTTPException(status_code=400, detail="Projekt ze obstaja")
    return crud.create_projekt(db=db, projekt=projekt)