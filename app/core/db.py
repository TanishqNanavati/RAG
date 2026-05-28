import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chat_history.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Connect args needed for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
