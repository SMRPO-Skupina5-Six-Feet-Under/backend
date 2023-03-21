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

# ============== ZGODBE ==============
#TODO get post put delete za zgodbe

#pridobi vse zgodbe v projektu z id-jem
@app.get("/stories/{project_id}", response_model=List[schemas.Story])
async def read_all_zgodbe_in_project(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_stories_in_project(db, project_id, skip=skip, limit=limit)

#pridobi eno zgodbo z id-jem
@app.get("/story/{id}", response_model=schemas.Story)
async def read_zgodba(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return db_story

#create story in project
@app.post("/story", response_model=schemas.Story)
async def create_story(story: schemas.StoryCreate, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_name(db, name=story.name)
    if db_story & db_story==story.projectId: #če zgodba z istim imenom že obstaja v projektu vrni ERROR 
        raise HTTPException(status_code=400, detail="Story already exists") 
    
    return crud.create_story(db=db, story=story)

#update story
@app.put("/story/{id}", response_model=schemas.Story)
async def update_story(id: int, story: schemas.Story, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, stroy_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")

    return crud.update_story_generic(db=db, story=story, story_id=id)

#update only sprint id of story 
@app.put("/story/{id}/sprint", response_model=schemas.Story)
async def update_story_sprint(id: int, story: schemas.Story, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")

    return crud.update_story_sprint_id(db=db, story=story, story_id=id)

#update isDone and endDate of story
@app.put("/story/{id}/isDone", response_model=schemas.Story)
async def update_story_isDone(id: int, story: schemas.Story, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, story_id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")

    return crud.update_story_isDone(db=db, story=story, story_id=id)

#delete story
@app.delete("/story/{id}", response_model=schemas.Story)
async def delete_story(id: int, db: Session = Depends(get_db)):
    db_story = crud.get_story_by_id(db, id=id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story does not exist")
    
    return crud.delete_story(db=db, story_id=id)