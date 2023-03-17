from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import List
from fastapi.middleware.cors import CORSMiddleware  # Middleware.
from app import crud, models, schemas  # Local import files.


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

# Init of db.
models.Base.metadata.create_all(bind=engine)

# CORE functionalities.

# Dependency.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Hello najbolsa SMRPO ekipa :)"}


@app.get("/projects", response_model=List[schemas.Project])
async def list_all_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_projects(db, skip=skip, limit=limit)


@app.get("/project", response_model=schemas.Project)
async def get_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.get_project(db=db, name=project.name)


@app.post("/project", response_model=schemas.Project)
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    # db_projekt = crud.getProjektbyName(db, imeProjekta=projekt.imeProjekta)
    # print(db_projekt.imeProjekta)
    # if db_projekt:
    #     raise HTTPException(status_code=400, detail="Projekt ze obstaja")
    return crud.create_project(db=db, project=project)
