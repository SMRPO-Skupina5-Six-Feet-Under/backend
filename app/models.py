from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, Date
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
    uporabniki = relationship("User", back_populates="projekt")
    stories = relationship("Story", back_populates="projekt")


class Story(Base):
    __tablename__ = "zgodba"

    #======================== atributi ========================
    id = Column(Integer, primary_key=True, index=True) #ID zgodbe

    name = Column(String)               #ime zgodbe
    storyDescription = Column(String)   #opis zgodbe
    priority = Column(String)           #prioriteta zgodbe  #TODO Must have, Should have, Could have, Won't have now
    businessValue = Column(Integer)     #poslovna vrednost zgodbe
    timeEstimate = Column(Integer)      #time estimate zgodbe
    isDone = Column(Boolean)            #ce je koncana nastavi na TRUE
    startDate = Column(Date, nullable=True) #datum ko je zgodba dodana
    endDate = Column(Date, nullable=True)   #datum ko je zgodba koncana

    #================= relacije/atrbuti drugje ==================
    #povezava s projektom
    projectId = Column(Integer, ForeignKey('project.id'))
    project = relationship("Project", back_populates="zgodbe")

    #TODO povezava s sprintom
    sprint_id = Column(Integer, ForeignKey('sprint.id'))
    sprint = relationship("Sprint", back_populates="stories")     #TODO popravi back_populates na to kar je v sprintu


    #TODO povezava z nalogami
    subtasks = relationship("Task", back_populates="story")     #TODO popravi back_populates na to kar je v sprintu

    