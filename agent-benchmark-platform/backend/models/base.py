"""Base declarative class for all SQLAlchemy models."""
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class Base(DeclarativeBase):
    def to_dict(self):
        """Serialize model columns to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

