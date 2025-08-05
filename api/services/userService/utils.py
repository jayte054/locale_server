from typing import Optional, Dict, List, Any
from pydantic import (
    BaseModel, 
    Field, 
    EmailStr, 
    field_validator,
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
    created_at: str
    updated_at: Optional[str] = None
    vendor_metadata: dict = {}
    userId: str

class VendorFilter(BaseModel):
    search: Optional[str] = None
    created_at: Optional[str] = None
    skip: Optional[int] = None
    take: Optional[int] = None

class FetchVendorResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    has_more: bool
