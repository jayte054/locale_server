from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum as PyEnum


@dataclass
class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    password: str


class UserRole(PyEnum):
    User = "user"
    Admin = "admin"
    Guest = "guest"


class UserStatus(PyEnum):
    PAID = 'paid'
    NOT_PAID = 'not_paid'


class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    hashed_password: str
    role: UserRole
    user_active: bool
    user_status: UserStatus
    user_metadata: dict = {}

    class Config:
        from_attributes = True
