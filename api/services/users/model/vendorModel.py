import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Enum,
    JSON,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Boolean,
)
from sqlalchemy.orm import relationship

from config.database import Base
from services.users.utils import VendorScale


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
        String(20),
        nullable=False,
        comment="Primary vendor number"
    )
    vendor_email = Column(
        String(50),
        nullable=True,
        comment="Primary vendor email"
    )
    vendor_merchandise = Column(
        String(100),
        nullable=False,
        comment="Type of goods"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="Record creation timestamp"
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        comment="last modification timestamp"
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
        comment="Business size classification"
    )
    is_active = Column(
        Boolean,
        nullable=True,
        default=True,
        comment="active or inactive status"
    )
    deleted = Column(
        Boolean,
        nullable=True,
        default=False,
        comment='delete a vendor'
    )
    vendor_metadata = Column(
        JSON,
        nullable=False,
        comment="Extended properties and attributes"
    )
    user_id = Column(
        String(36),
        ForeignKey('users.id'),
        nullable=False
    )
    user = relationship(
        "User",
        back_populates="vendors",
    )

    # Table Constraints
    __table_args__ = (
        CheckConstraint(
            "vendor_rating BETWEEN 1 and 5",
            name="ck_vendor_rating_range"
        ),
    )
