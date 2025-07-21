import datetime
from pydantic import Field, BaseModel
from services.authService.utils import UserRole, UserStatus


class CreateUserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    password: str = Field(..., min_length=8)


class Config:
    from_attributes = True
