from sqlalchemy.orm import Session

from app import models
from app import schemas

# get za projekt z imenom
def get_projekt(db: Session, imeProjekta: str):
    return db.query(models.Projekt).filter(models.Projekt.imeProjekta == imeProjekta).first()

# get za vse projekte
def get_all_projekti(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Projekt).offset(skip).limit(limit).all()

# create za projekt
def create_projekt(db: Session, projekt: schemas.ProjektCreate):
    db_projekt = models.Projekt(imeProjekta=projekt.imeProjekta)
    db.add(db_projekt)
    db.commit()
    db.refresh(db_projekt)
    return db_projekt

#TODO potrebne operacije za prijavo
#to dela anze

#TODO potrebne operacije za zgodbe
#to dela anze

#get zgodba by name 
def get_story(db: Session, name: str):
    return db.query(models.Story).filter(models.Story.anme == name).first()

#ustvari novo zgodbo
def create_story(db: Session, story: schemas.StoryCreate):
    db_story = models.Story(name=story.name, storyDescription=story.storyDescription, priority=story.priority, businessValue=story.businessValue, timeEstimate=story.timeEstimate, startDate=story.startDate, projectId=story.projectId) 
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
def update_story_generic(db: Session, story: schemas.Story, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    #posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.name = db_new_story.name if story.name == None else story.name
    db_new_story.storyDescription = db_new_story.storyDescription if story.storyDescription == None else story.storyDescription
    db_new_story.priority = db_new_story.priority if story.priority == None else story.priority
    db_new_story.businessValue = db_new_story.businessValue if story.businessValue == None else story.businessValue
    db_new_story.timeEstimate = db_new_story.timeEstimate if story.timeEstimate == None else story.timeEstimate
    db_new_story.endDate = db_new_story.endDate if story.endDate == None else story.endDate
    db_new_story.sprint_id = db_new_story.sprint_id if story.sprint_id == None else story.sprint_id

    db.commit()
    db.refresh(db_new_story)

    return db_new_story

# update only sprint_id
def update_story_sprint_id(db: Session, story: schemas.Story, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    #posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.sprint_id = db_new_story.sprint_id if story.sprint_id == None else story.sprint_id

    db.commit()
    db.refresh(db_new_story)

    return db_new_story

#update only end date
def update_story_end_date(db: Session, story: schemas.Story, story_id: int):
    db_new_story = db.query(models.Story).filter(models.Story.id == story_id).first()

    #posodobi vrednosti če so podane drugače ostanejo stare
    db_new_story.endDate = db_new_story.endDate if story.endDate == None else story.endDate

    db.commit()
    db.refresh(db_new_story)

    return db_new_story

# delete story
def delete_story(db: Session, story_id: int):
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    db.delete(db_story)
    db.commit()
    return db_story