from sqlalchemy import Column, String, Integer, Boolean, DateTime
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
    productOwner = Column(String(256))
    scrumMaster = Column(String(256))
    developers = Column(String(256))


class ProjectDevelopers(Base):
    __tablename__ = "project_developers"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(256))
