"""SystemSetting model for platform configuration."""
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, utc_now_iso

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(255), default="")
    updated_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

