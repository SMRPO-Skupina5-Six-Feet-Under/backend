from sqlalchemy.orm import Session

import models
import schemas

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

# TODO potrebne operacije za uporabnika in projkete