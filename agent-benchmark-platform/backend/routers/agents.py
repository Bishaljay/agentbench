"""Agent Registry management routes."""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, AgentVersion, AgentCapability, AuditLog, User
from schemas import AgentIn, AgentUpdate, AgentOut
from security import get_current_user
from sdk.builtin import AGENT_REGISTRY, perform_operation

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.get("", response_model=List[AgentOut])
def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered agents."""
    agents = db.scalars(select(Agent).order_by(Agent.id)).all()
    return [
        AgentOut(
            id=a.id,
            name=a.name,
            kind=a.kind,
            version=a.version or "1.0.0",
            capabilities=a.capabilities or "deterministic",
            description=a.description or "",
            created_at=a.created_at or ""
        )
        for a in agents
    ]

@router.post("", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
def create_agent(
    data: AgentIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new trusted agent implementation."""
    if data.kind.lower() not in AGENT_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only trusted built-in implementations are allowed: {list(AGENT_REGISTRY.keys())}"
        )

    existing = db.scalar(select(Agent).where(Agent.name == data.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with name '{data.name}' already exists"
        )

    agent = Agent(
        name=data.name,
        kind=data.kind.lower(),
        version=data.version,
        capabilities=data.capabilities,
        description=data.description
    )
    db.add(agent)
    db.flush()

    # Create initial version entry
    db.add(AgentVersion(
        agent_id=agent.id,
        version=data.version,
        changelog="Initial registration"
    ))

    # Add audit log
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="agent_registered",
        entity_type="agent",
        entity_id=str(agent.id),
        details=json.dumps({"name": agent.name, "kind": agent.kind})
    ))

    db.commit()
    db.refresh(agent)
    return AgentOut(
        id=agent.id,
        name=agent.name,
        kind=agent.kind,
        version=agent.version,
        capabilities=agent.capabilities,
        description=agent.description,
        created_at=agent.created_at or ""
    )

@router.get("/{agent_id}", response_model=AgentOut)
def get_agent_details(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full details of an agent."""
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(
        id=agent.id,
        name=agent.name,
        kind=agent.kind,
        version=agent.version or "1.0.0",
        capabilities=agent.capabilities or "deterministic",
        description=agent.description or "",
        created_at=agent.created_at or ""
    )

@router.put("/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: int,
    data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update agent metadata or version."""
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if data.name and data.name != agent.name:
        existing = db.scalar(select(Agent).where(Agent.name == data.name))
        if existing:
            raise HTTPException(status_code=409, detail="Agent name already in use")
        agent.name = data.name

    if data.version and data.version != agent.version:
        agent.version = data.version
        db.add(AgentVersion(
            agent_id=agent.id,
            version=data.version,
            changelog="Updated agent version"
        ))

    if data.capabilities is not None:
        agent.capabilities = data.capabilities
    if data.description is not None:
        agent.description = data.description

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="agent_updated",
        entity_type="agent",
        entity_id=str(agent.id)
    ))
    db.commit()
    db.refresh(agent)
    return AgentOut(
        id=agent.id,
        name=agent.name,
        kind=agent.kind,
        version=agent.version,
        capabilities=agent.capabilities,
        description=agent.description,
        created_at=agent.created_at or ""
    )

@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an agent from registry."""
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    name = agent.name
    db.delete(agent)
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="agent_deleted",
        entity_type="agent",
        entity_id=str(agent_id),
        details=json.dumps({"name": name})
    ))
    db.commit()
    return {"message": f"Agent '{name}' successfully deleted"}

@router.post("/{agent_id}/validate")
def validate_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate agent operational behavior on a sample calculation."""
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        sample_out = perform_operation("sum", {"numbers": [10, 20, 30]})
        valid = (sample_out == 60)
        return {
            "status": "valid" if valid else "invalid",
            "kind": agent.kind,
            "test_operation": "sum",
            "test_output": sample_out,
            "expected": 60
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

