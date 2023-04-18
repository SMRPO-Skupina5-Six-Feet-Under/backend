from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    email: str
    isAdmin: bool
    password: str
    lastLogin: Optional[datetime]
    userDeleted: Optional[bool]

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
    id: int
    name: str
    description: str
    documentation: str
    isAlive: bool = True
    projectParticipants: List[ProjectParticipantsInput]

    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    name: str
    description: str
    projectParticipants: List[ProjectParticipantsInput]

    class Config:
        orm_mode = True


class ProjectDataPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True


class ProjectDataPatchResponse(BaseModel):
    id: int
    name: str
    description: str
    isAlive: bool

    class Config:
        orm_mode = True


class Sprint(BaseModel):
    id: int
    startDate: datetime
    endDate: datetime
    velocity: float
    projectId: int

    class Config:
        orm_mode = True


class SprintCreate(BaseModel):
    startDate: datetime
    endDate: datetime
    velocity: float

    class Config:
        orm_mode = True


class SprintPatch(BaseModel):
    startDate: Optional[datetime]
    endDate: Optional[datetime]
    velocity: Optional[float]

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


class AcceptenceTestBase(BaseModel):
    description: str


class AcceptenceTestCreate(AcceptenceTestBase):
    pass


class AcceptenceTest(AcceptenceTestBase):
    id: int
    storyId: int

    class Config:
        orm_mode = True


class StoryBase(BaseModel):
    name: str
    storyDescription: str
    priority: str
    businessValue: int
    timeEstimate: int

    projectId: int


class StoryCreate(StoryBase):
    pass


class StoryUpdate(StoryBase):
    sprint_id: int = None
    isDone: bool = False

##for only updating the time estiamte
class StoryUpdateTime(BaseModel):
    timeEstimate: int


class Story(StoryBase):
    id: int

    sprint_id: int = None
    isDone: bool = False

    acceptenceTests: list[AcceptenceTest] = []
    timeEstimateOriginal: int = None

    # TODO povezava z nalogami
    # subtasks: List["Task"] = []
    class Config:
        orm_mode = True


class Task(BaseModel):
    id: int
    name: str
    description: str
    timeEstimate: int
    assigneeUserId: int = None
    hasAssigneeConfirmed: bool = False
    isActive: bool = False
    isFinished: bool = False
    storyId: int

    class Config:
        orm_mode = True


class TaskInput(BaseModel):
    name: str
    description: str
    timeEstimate: int
    assigneeUserId: Optional[int] = None

    class Config:
        orm_mode = True


class WorkTime(BaseModel):
    id: int
    taskId: int
    userId: int
    date: datetime
    timeDone: int
    timeRemainingEstimate: int

    class Config:
        orm_mode = True


class WorkTimeInput(BaseModel):
    date: datetime
    timeDone: int
    timeRemainingEstimate: int

    class Config:
        orm_mode = True


class Message(BaseModel):
    id: int
    content: str
    timestamp: datetime
    userId: int
    projectId: int

    class Config:
        orm_mode = True


class MessageInput(BaseModel):
    content: str

    class Config:
        orm_mode = True


class ProjectDocumentation(BaseModel):
    text: str

    class Config:
        orm_mode = True
