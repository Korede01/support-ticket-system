from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from app.db.session import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    jti = Column(String, unique=True, index=True, nullable=False)
    token_type = Column(String, nullable=False)  # "access" or "refresh"
    blacklisted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
