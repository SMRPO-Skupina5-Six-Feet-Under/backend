import datetime

from pydantic import BaseModel, Field
from typing import List, Optional
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

class UserCreate(BaseModel):
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
    permissions: Optional[str]


class Config:
        orm_mode = True

## tega ni v BAZI (DTO objekt!!
class LogInData(BaseModel):
  userName: str
  password: str

"""-----------EXAMPLES------------"""
#Create class
#class UporabnikCreate(UserBase): 
#    pass

#končni class
#class Uporabnik(UserBase): 
#    id: int
#    projekt_id: int 

#    class Config:
#        orm_mode = True

#shema za projekt

#base class
#class ProjektBase(BaseModel):
#    imeProjekta: str

#Create class
#class ProjektCreate(ProjektBase): 
#    pass

#končni class
#class Projekt(ProjektBase):
#    id: int
#    uporabniki: List[Uporabnik] = []

#    class Config:
#        orm_mode = True







