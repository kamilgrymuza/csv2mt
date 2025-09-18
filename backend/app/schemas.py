from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    clerk_id: str


class UserUpdate(UserBase):
    pass


class User(UserBase):
    id: int
    clerk_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime