import datetime

from sqlalchemy.orm import Session

from app import models
from app import schemas


#-------USERS-------
# gets all users
def get_all_users(db: Session):
    return db.query(models.User).all()

# gets the user by id

# creates a new user
def create_user(db: Session, user: schemas.UserCreate):
    new_user = models.User(userName = user.userName, firstName = user.firstName, lastName = user.lastName, email = user.email, isAdmin = user.isAdmin, password = user.password, permissions = user.permissions)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

# check if user with username exists
def check_user_username_exist(db: Session, uUserName: str):
    return db.query(models.User).filter(models.User.userName == uUserName).first()

# check if user with email exists
def check_user_email_exist(db: Session, uEmail: str):
    return db.query(models.User).filter(models.User.email == uEmail).first()



"""-----------EXAMPLES------------"""
# get za projekt z imenom
#def get_projekt(db: Session, imeProjekta: str):
#    return db.query(models.Projekt).filter(models.Projekt.imeProjekta == imeProjekta).first()


# get za vse projekte
#def get_all_projekti(db: Session, skip: int = 0, limit: int = 100):
#    return db.query(models.Projekt).offset(skip).limit(limit).all()


# create za projekt
#def create_projekt(db: Session, projekt: schemas.ProjektCreate):
#    db_projekt = models.Projekt(imeProjekta=projekt.imeProjekta)
#    db.add(db_projekt)
#    db.commit()
#    db.refresh(db_projekt)
#    return db_projekt


# TODO potrebne operacije za uporabnika in projkete

def get_UporabnikBase_by_username(db: Session, userName: str):
    return db.query(models.User).filter(models.User.userName == userName).first()

def setUserLogInTime(db: Session, userId: int):
    user: schemas.UserBase = db.query(models.User).filter(models.User.id == userId).first()
    if(user != None):
        user.lastLogin = datetime.datetime.now().astimezone()
        db.commit()



