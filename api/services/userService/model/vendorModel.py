import uuid
from sqlalchemy import Column, String, Integer, Enum, JSON, DateTime, ForeignKey

from config.database import Base
from services.userService.utils import VendorScale

class Vendor(Base):
    __tablename__ = 'vendors'
    id = Column(
        String(36), 
        primary_key=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
        )
    vendor_title = Column(
        String(100), 
        index=True, 
        nullable=False,
        comment="Official business name"
        )
    vendor_location = Column(
        String(100), 
        nullable=False,
        comment="city/state"
        )
    vendor_address = Column(
        String(200), 
        nullable=False,
        comment="full physical address"
        )
    vendor_contact = Column(
        String(11), 
        nullable=False,
        comment="Primary vendor number"
        )
    vendor_email = Column(
        String(50),
        nullable=False,
        comment="Primary vendor email"
    )
    vendor_merchandise = Column(
        String(100), 
        nullable=False,
        comment = "Type of goods"
        )
    created_at = Column(
        DateTime,  
        nullable=False,
        comment= "Record creation timestamp"
        )
    vendor_rating = Column(
        Integer, 
        nullable=False, 
        info={"check": "vendor_rating BETWEEN 1 AND 5"},
        comment="Customer rating (1-5 scale)"
        )
    vendor_scale = Column(
        Enum(VendorScale), 
        index=True, 
        nullable=False,
        comment= "Business size classification"
        )
    vendor_metadata = Column(
        JSON,
        comment="Extended properties and attributes"
        )
    user_id = Column(
        String,
        ForeignKey('users.id'),
        nullable=False)