from pydantic import BaseModel
from typing import Optional
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
    permissions: str
    lastLogin: datetime

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


class Project(BaseModel):
    name: str
    id: int
    productOwner: str
    scrumMaster: str
    developers: str  # List[UserName]

    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    name: str
    productOwner: str
    scrumMaster: str
    developers: str  # List[UserName]

    class Config:
        orm_mode = True
