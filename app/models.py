from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from .database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String(256), unique=True)
    firstName = Column(String(256))
    lastName = Column(String(256))
    email = Column(String(256), unique=True)
    isAdmin = Column(Boolean, default=False)
    password = Column(String(128))
    permissions = Column(String, nullable=True)
    lastLogin = Column(DateTime, nullable=True)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256))


class ProjectParticipants(Base):
    __tablename__ = "project_participants"

    id = Column(Integer, primary_key=True, index=True)

    roleId = Column(Integer)

    projectId = Column(Integer, ForeignKey("project.id"))
    userId = Column(Integer, ForeignKey("user.id"))
