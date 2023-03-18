import datetime

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


#Shema za uporabnika 

#base class
class UserBase(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
    permissions: str
    lastLogin: datetime

#Create class
class UserCreate(UserBase):
    pass

#končni class
class User(UserBase):
    id: int
    projekt_id: int 

    class Config:
        orm_mode = True

#shema za projekt

#base class
class ProjektBase(BaseModel):
    imeProjekta: str

#Create class
class ProjektCreate(ProjektBase): 
    pass

#končni class
class Projekt(ProjektBase):
    id: int
    uporabniki: List[User] = []

    class Config:
        orm_mode = True





## tega ni v BAZI (DTO objekt!!
class LogInData(BaseModel):
  userName: str
  password: str
