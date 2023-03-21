from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class UserBase(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
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

    class Config:
        orm_mode = True


# ============================= SHEMA ZA STORY =============================

#base class
class StoryBase(BaseModel):
    name: str
    storyDescription: str
    priority: str
    businessValue: int
    timeEstimate: int
    startDate: datetime
    projectId: int

#Create class
class StoryCreate(StoryBase):
    pass

#končni class
class Story(StoryBase):
    id: int

    isDone: bool = False
    endDate: datetime = None

    sprint_id: int = None

    #TODO povezava z nalogami
    #subtasks: List["Task"] = []
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


class Sprint(BaseModel):
    id: int
    startDate: date
    endDate: date
    velocity: float
    projectId: int

    class Config:
        orm_mode = True


class SprintCreate(BaseModel):
    startDate: date
    endDate: date
    velocity: float

    class Config:
        orm_mode = True


class ProjectRole(BaseModel):
    id: int
    role: str


# tega ni v BAZI (DTO objekt)!!
class LogInData(BaseModel):
    userName: str
    password: str


class ChangePasswordData(BaseModel):
    newPassword: str
