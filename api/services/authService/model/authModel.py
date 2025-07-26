import uuid
from sqlalchemy import (
    Column, 
    String, 
    DateTime, 
    Boolean, 
    JSON, 
    Enum, 
    func,
    )
from sqlalchemy.orm import relationship

from config.database import Base
from services.authService.utils import UserRole, UserStatus


class User(Base):
    __tablename__ = 'users'
    id = Column(
        String(36), 
        primary_key=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
        )
    email = Column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=False
        )
    first_name = Column(
        String(100), 
        nullable=False
        )
    last_name = Column(
        String(100), 
        nullable=False
        )
    phone_number = Column(
        String(11), 
        nullable=False
        )
    hashed_password = Column(
        String(60), 
        nullable=False
        )
    created_at = Column(
        DateTime, 
        index=True, 
        nullable=True
        )
    role = Column(
        Enum(UserRole), 
        default=UserRole.Guest, 
        index=True
        )
    user_active = Column(
        Boolean, 
        index=True, 
        nullable=False
        )
    user_status = Column(
        Enum(UserStatus), 
        default=UserStatus.Inactive_user, 
        index=True, 
        nullable=False
        )
    user_metadata = Column(JSON)
    vendors = relationship(
        "Vendor",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"
