from pydantic import BaseModel, Field
from typing import List


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