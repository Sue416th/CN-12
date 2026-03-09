from typing import Generator

from app.agents.orchestrator import AgentOrchestrator
from app.db.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()
