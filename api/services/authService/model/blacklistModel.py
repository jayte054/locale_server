import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Enum, func

from config.database import Base


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    token = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    expires = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow)
