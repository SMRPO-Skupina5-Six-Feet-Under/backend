from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

#TODO samo osnova, dodaj atribute in vse potrebno
class Uporabnik(Base):
    __tablename__ = "uporabnik"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeUporabnika = Column(String)

    #relacije/atributi drugje
    projekt_id = Column(Integer, ForeignKey('projekt.id'))
    projekt = relationship("Projekt", back_populates="uporabniki")



class Projekt(Base):
    __tablename__ = "projekt"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeProjekta = Column(String)

    #relacije/atrbuti drugje 
    uporabniki = relationship("Uporabnik", back_populates="projekt")
