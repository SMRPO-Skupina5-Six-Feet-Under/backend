from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


#Shema za uporabnika 

#base class
class UporabnikBase(BaseModel):  
    imeUporabnika: str

#Create class
class UporabnikCreate(UporabnikBase): 
    pass

#končni class
class Uporabnik(UporabnikBase): 
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
    uporabniki: List[Uporabnik] = []

    class Config:
        orm_mode = True




# ============================= SHEMA ZA STORY =============================

#base class
class StoryBase(BaseModel):
    name: str
    storyDescription: str
    priority: str
    businessValue: int
    timeEstimate: int
    startDate: datetime
    projectId: int

#Create class
class StoryCreate(StoryBase):
    pass

#končni class
class Story(StoryBase):
    id: int

    isDone: bool = False
    endDate: datetime = None

    sprint_id: int = None

    #TODO povezava z nalogami
    #subtasks: List["Task"] = []
    class Config:
        orm_mode = True