from typing import Optional, Dict, List, Any
from pydantic import (
    BaseModel, 
    Field, 
    EmailStr, 
    field_validator,
    ConfigDict,
    )
from enum import Enum as PyEnum
from dataclasses import dataclass
from datetime import datetime


class VendorScale(PyEnum):
    Retail = "Retail"
    Wholesale = "Wholesale"


@dataclass
class CreateVendorRequest(BaseModel):
    vendor_title: str = Field(..., min_length=1, max_length=100)
    vendor_location: str = Field(..., min_length=2, max_length=100)
    vendor_address: str = Field(..., min_length=5, max_length=200)
    vendor_contact: str = Field(..., min_length=5, max_length=20)
    vendor_email: EmailStr
    vendor_merchandise: str = Field(..., min_length=2, max_length=100)
    vendor_scale: VendorScale

    @field_validator('vendor_title')
    @classmethod
    def validate_title(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v.title()
    
    @field_validator('vendor_contact')
    @classmethod
    def validate_contact(cls, v: str):
        if not any(char.isdigit() for char in v):
            raise ValueError("Contact should contain at least one digit")
        return v


class CreateVendorResponse(BaseModel):
    id: str
    vendor_title: str
    vendor_location: str
    vendor_address: str
    vendor_contact: str
    vendor_email: str
    vendor_merchandise: str
    vendor_scale: VendorScale
    vendor_rating: int
    created_at: str
    updated_at: Optional[str] = None
    vendor_metadata: dict = {}
    is_active: bool
    deleted: bool
    userId: str

@dataclass
class VendorFilter:
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None
    created_at: Optional[str] = None
    skip: Optional[int] = None
    take: Optional[int] = None

    @field_validator('created_at', mode='before')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, '%d-%m-%y')
            except ValueError:
                raise ValueError("Date must be in DD-MM-YYYY format")
        return v

    @field_validator('take', mode = 'before')
    @classmethod
    def validate_take(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v <= 0 or v > 500):
            raise ValueError("Take must be between 1 and 500")
        return v

    model_config = ConfigDict(extra='forbid')

class FetchVendorResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    has_more: bool

@dataclass
class UpdateVendorInput:
    vendor_title: Optional[str] = None
    vendor_location: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_contact: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_merchandise: Optional[str] = None
    vendor_rating: Optional[int] = None
    vendor_scale: Optional[VendorScale] = None
    vendor_metadata: Optional[Dict[str, Any]] = None


class VendorResponse(BaseModel):
    id: str
    vendor_title: str
    vendor_location: str
    vendor_address: str
    vendor_contact: str
    vendor_email: str
    vendor_merchandise: str
    vendor_scale: VendorScale
    vendor_rating: int
    created_at: str
    updated_at: Optional[str] = None
    vendor_metadata: dict = {}
    is_active: Any #convert to boolean when moving to staging
    deleted: Any #convert to boolean when moving to staging
    userId: str