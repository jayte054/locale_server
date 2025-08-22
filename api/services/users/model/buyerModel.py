import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    JSON,
    Index,
    ForeignKey
)
from sqlalchemy.orm import relationship

from config.database import Base

class Buyer(Base):
    __tablename__ = 'buyers'
    id = Column(
        String(36),
        primary_key = True,
        index = True,
        default = lambda: str(uuid.uuid4())
    )
    buyer_name = Column(
        String(100),
        index=True,
        nullable=False,
        comment='buyer full name'
    )
    buyer_email = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    buyer_location = Column(
        String(100),
        nullable=False,
        comment= 'city/state'
    )
    buyer_address = Column(
        String(200),
        nullable=False,
        comment='full physical address'
    )
    buyer_contact = Column(
        String(11),
        nullable=False,
        comment='buyer phone number'
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment='Record creation timestamp'
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        comment='last modification timestamp'
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='active or inactive status'
    )
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        comment='deleted status'
    )
    buyer_metadata = Column(
        JSON,
        nullable=False,
        default=dict,
        comment='Extended properties and attributes'
    )
    user_id = Column(
        String(36),
        ForeignKey('users.id'),
        nullable=False
    )
    user = relationship(
        "User",
        back_populates='buyers',
        lazy="select"
    )

    #Indexes
    __table_args__ = (
        Index('idx_buyer_email_active', 'buyer_email', 'is_active'),
        Index('idx_buyer_user', 'user_id')
    )

    # Table Constraints
    # __table_args__ = (
    #     CheckConstraint(
    #         'v'
    #     )
    # )
