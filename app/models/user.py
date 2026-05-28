from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime, timezone
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class GuestUsage(Base):
    __tablename__ = "guest_usages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    message_count = Column(Integer, default=0)
    upload_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
