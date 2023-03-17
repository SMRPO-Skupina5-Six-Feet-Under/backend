from pydantic import BaseModel, Field
from typing import List


#Shema za uporabnika 

#base class
class UserBase(BaseModel):
    imeUporabnika: str

#Create class
class UporabnikCreate(UserBase):
    pass

#končni class
class User(UserBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True

#shema za projekt

#base class
class ProjectBase(BaseModel):
    name: str

#Create class
class ProjectCreate(ProjectBase):
    pass

#končni class
class Project(ProjectBase):
    id: int
    users: List[User] = []

    class Config:
        orm_mode = True