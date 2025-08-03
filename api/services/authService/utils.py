from typing import Optional
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
    New_User = 'New_User'
    Active_User = 'Active_User'
    Inactive_user = 'Inactive_user'
    Loyal_customer = 'Loyal_Customer'


class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    role: UserRole
    user_active: bool
    user_status: UserStatus
    email_validated: bool
    user_metadata: dict = {}

    class Config:
        from_attributes = True

class User(BaseModel):
    email: str
    name: str
    id: str
    contact: str
    role: str
    status: str
    metadata: dict = {}

class SignInResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: str
    token_type: str
    access_token_expires_in: int
    refresh_token_expires_in: int

class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str

class LogoutResponse(BaseModel):
    status: str
    message: str
    timestamp: str

class UpdateUserInterface(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    user_active: Optional[bool] = None
    user_status: Optional[UserStatus] = None
    email_validated: Optional[bool] = None
    user_metadata: Optional[dict] = None

class VerifyTokenResponse(BaseModel):
    message: str