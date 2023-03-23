from sqlalchemy import Column, Integer, Boolean, DateTime, Date, ForeignKey, Float, String
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String(256), unique=True)
    firstName = Column(String(256))
    lastName = Column(String(256))
    email = Column(String(256), unique=True)
    isAdmin = Column(Boolean, default=False)
    password = Column(String(128))
    lastLogin = Column(DateTime, nullable=True)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256))
    description = Column(String)


class ProjectParticipants(Base):
    __tablename__ = "project_participants"

    id = Column(Integer, primary_key=True, index=True)

    roleId = Column(Integer)

    projectId = Column(Integer, ForeignKey("project.id"))
    userId = Column(Integer, ForeignKey("user.id"))


class Sprint(Base):
    __tablename__ = "sprint"

    id = Column(Integer, primary_key=True, index=True)
    startDate = Column(Date, nullable=True)
    endDate = Column(Date, nullable=True)
    velocity = Column(Float)

    projectId = Column(Integer, ForeignKey("project.id"))


class Story(Base):
    __tablename__ = "story"

    # ======================== atributi ========================
    id = Column(Integer, primary_key=True, index=True)  # ID zgodbe

    name = Column(String)               # ime zgodbe
    storyDescription = Column(String)   # opis zgodbe
    priority = Column(String)           # prioriteta zgodbe  # TODO Must have, Should have, Could have, Won't have now
    businessValue = Column(Integer)     # poslovna vrednost zgodbe
    timeEstimate = Column(Integer)      # time estimate zgodbe
    isDone = Column(Boolean)            # ce je koncana nastavi na TRUE
    startDate = Column(Date, nullable=True)  # datum ko je zgodba dodana
    endDate = Column(Date, nullable=True)   # datum ko je zgodba koncana

    # ================= relacije/atrbuti drugje ==================
    # sprejemni testi
    acceptenceTests = relationship("AcceptenceTest", back_populates="story")

    # povezava s projektom
    projectId = Column(Integer, ForeignKey('project.id'))
    # project = relationship("Project", back_populates="zgodbe")

    # TODO povezava s sprintom
    sprint_id = Column(Integer, ForeignKey('sprint.id'))
    # sprint = relationship("Sprint", back_populates="stories")     #TODO popravi back_populates na to kar je v sprintu

    # TODO povezava z nalogami
    # subtasks = relationship("Task", back_populates="story")     #TODO popravi back_populates na to kar je v nalogah


class AcceptenceTest(Base):
    __tablename__ = "acceptence_test"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    isDone = Column(Boolean)

    # ================= relacije/atrbuti drugje ==================
    storyId = Column(Integer, ForeignKey('story.id'))
    story = relationship("Story", back_populates="acceptenceTests")


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    timeEstimate = Column(Integer)
    assigneeUserId = Column(Integer, nullable=True)
    hasAssigneeConfirmed = Column(Boolean, default=False)
    isActive = Column(Boolean, default=False)
    isDone = Column(Boolean, default=False)

    storyId = Column(Integer, ForeignKey("story.id"))
