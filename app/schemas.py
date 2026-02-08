from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class UserRole(str,Enum):
    USER = "user"
    ADMIN = "admin"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: int # who assigned this to who

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    owner_id: int
    created_at: datetime