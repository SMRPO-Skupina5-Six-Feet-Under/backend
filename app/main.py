from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import List
from fastapi.middleware.cors import CORSMiddleware  # Middleware.
from app import crud, models, schemas  # Local import files.


app = FastAPI(
    title="SMRPO Backend API",
    description="API for backend of SMRPO project.",
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


# Dependency.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Backend is up and running."}


@app.get("/projects", response_model=List[schemas.Project], tags=["Projects"])
async def list_all_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_projects(db, skip=skip, limit=limit)


@app.get("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def get_project(identifier: int, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, identifier=identifier)
    if not db_project:
        raise HTTPException(status_code=400, detail="Project with given identifier does not exist.")
    return db_project


@app.post("/project", response_model=schemas.Project, tags=["Projects"])
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    # TODO: Add check if admin...Or should this be checked by frontend?
    db_project = crud.get_project_by_name(db=db, name=project.name)
    if db_project:
        raise HTTPException(status_code=400, detail="Project with such name already exist.")
    return crud.create_project(db=db, project=project)


@app.delete("/project/{identifier}", response_model=schemas.Project, tags=["Projects"])
async def delete_project(identifier: int, db: Session = Depends(get_db)):
    # We assume that frontend always serves only projects that actually exist.
    # Therefore, there is no need for additional check on backend.
    return crud.delete_project(db=db, identifier=identifier)
