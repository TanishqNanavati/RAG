from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime, timezone
from app.core.db import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
