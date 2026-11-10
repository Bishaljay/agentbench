"""Agent, AgentVersion, and AgentCapability models."""
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    capabilities: Mapped[str] = mapped_column(Text, default="deterministic")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    versions: Mapped[List["AgentVersion"]] = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    capability_items: Mapped[List["AgentCapability"]] = relationship("AgentCapability", back_populates="agent", cascade="all, delete-orphan")
    runs: Mapped[List["Run"]] = relationship("Run", back_populates="agent")

class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(50))
    code_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    changelog: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="versions")

class AgentCapability(Base):
    __tablename__ = "agent_capabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    parameters: Mapped[str] = mapped_column(Text, default="{}")

    agent: Mapped["Agent"] = relationship("Agent", back_populates="capability_items")

