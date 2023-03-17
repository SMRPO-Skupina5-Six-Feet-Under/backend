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
def get_zgodba(db: Session, imeZgodbe: str):
    return db.query(models.Zgodba).filter(models.Zgodba.imeZgodbe == imeZgodbe).first()

#ustvari novo zgodbo
#zaenkrat brez preverjanja ali že obstaja
def create_zgodba(db: Session, zgodba: schemas.ZgodbaCreate):
    db_zgodba = models.Zgodba(imeZgodbe=zgodba.imeZgodbe)
    db.add(db_zgodba)
    db.commit()
    db.refresh(db_zgodba)
    return db_zgodba

# TODO potrebne operacije za zgodbe
#to dela anze


# TODO potrebne operacije za uporabnika in registracijo
#to dela matic 

# TODO potreben opreacije za projekt
#to dela gasper 

# TODO potrebne operacije za naloge (task ali subtask)
#to se noben ni calimu

