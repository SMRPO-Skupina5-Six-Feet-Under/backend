from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LogInData(BaseModel):
    userName: str
    password: str


class UserBase(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
    permissions: Optional[str]
    lastLogin: Optional[datetime]

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
    permissions: Optional[str]

    class Config:
        orm_mode = True


class ProjectParticipantsInput(BaseModel):
    roleId: int
    userId: int

    class Config:
        orm_mode = True


class ProjectParticipants(BaseModel):
    roleId: int
    projectId: int
    userId: int

    class Config:
        orm_mode = True


class Project(BaseModel):
    name: str
    id: int
    projectParticipants: List[ProjectParticipantsInput]

    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    name: str
    projectParticipants: List[ProjectParticipantsInput]

    class Config:
        orm_mode = True


class ProjectRole(BaseModel):
    id: int
    role: str
