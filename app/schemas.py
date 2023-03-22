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

# ============================= SHEMA ZA ACCEPTENCE TEST =============================


class AcceptenceTestBase(BaseModel):
    description: str


class AcceptenceTestCreate(AcceptenceTestBase):
    pass


class AcceptenceTest(AcceptenceTestBase):
    id: int
    storyId: int

    class Config:
        orm_mode = True


# ============================= SHEMA ZA STORY =============================

# base class
class StoryBase(BaseModel):
    name: str
    storyDescription: str
    priority: str
    businessValue: int
    timeEstimate: int
    startDate: date
    projectId: int


# Create class
class StoryCreate(StoryBase):
    pass


# končni class
class StoryUpdate(StoryBase):
    endDate: date = None
    sprint_id: int = None
    isDone: bool = False


class Story(StoryBase):
    id: int

    endDate: date = None
    sprint_id: int = None
    isDone: bool = False

    acceptenceTests: list[AcceptenceTest] = []

    # TODO povezava z nalogami
    # subtasks: List["Task"] = []
    class Config:
        orm_mode = True


class Task(BaseModel):
    id: int
    name: str
    description: str
    timeEstimate: int
    assignee: str
    assignee_confirmed: bool
    storyId: int

    class Config:
        orm_mode = True


class TaskInput(BaseModel):
    name: str
    description: str
    timeEstimate: int
    assignee: str

    class Config:
        orm_mode = True
