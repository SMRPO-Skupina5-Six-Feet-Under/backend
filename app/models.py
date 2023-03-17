from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "user"

    # Attributes.
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    username = Column(String)
    email = Column(String)
    permission = Column(String)
    password = Column(String)
    last_session = Column(DateTime)

    # Relations.
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship("Project", back_populates="users")


class Project(Base):
    __tablename__ = "project"

    # Attributes.
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner = Column(String)
    scrum_master = Column(String)
    participants = Column(String)

    # Relations.
    users = relationship("User", back_populates="project")
