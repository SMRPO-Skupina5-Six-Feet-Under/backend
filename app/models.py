from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

from .database import Base

#TODO samo osnova, dodaj atribute in vse potrebno
class Uporabnik(Base):
    __tablename__ = "uporabnik"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String(256), unique=True)
    firstName = Column(String(256))
    lastName = Column(String(256))
    email = Column(String(256), unique=True)
    isAdmin = Column(Boolean, default=False)
    password = Column(String(128))
    permissions = Column(String)
    lastLogin = Column(DateTime)

    #relacije/atributi drugje
    projekt_id = Column(Integer, ForeignKey('projekt.id'), nullable=True)
    projekt = relationship("Projekt", back_populates="uporabniki")



class Projekt(Base):
    __tablename__ = "projekt"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeProjekta = Column(String)

    #relacije/atrbuti drugje 
    uporabniki = relationship("Uporabnik", back_populates="projekt")
