from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base

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
    zgodbe = relationship("Zgodba", back_populates="projekt")


class Zgodba(Base):
    __tablename__ = "zgodba"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeZgodbe = Column(String)
    opisZgodbe = Column(String)

    # tega poda uporabnik (po želji) če ga ne doda bo isti ID-ju? zaenkrat ga more podat in je lahko tudi podvojen
    userGiven_id_zgodbe = Column(Integer) 

    #relacije/atrbuti drugje 
    
    #zgodba je povezana na projekt potem pa se jo lahko premika še v sprint znotraj projekta

    #povezava s projektom
    projekt_id = Column(Integer, ForeignKey('projekt.id'))
    projekt = relationship("Projekt", back_populates="zgodbe")

    #TODO povezava s sprintom

    #TODO povezava z nalogami
    