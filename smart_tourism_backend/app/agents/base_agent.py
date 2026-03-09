from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accepts a context dict (e.g., user info, current itinerary state),
        returns updated context or results.
        """
        raise NotImplementedError

    def _get_monitor(self):
        """获取监控器"""
        try:
            from app.services.agent_monitor import get_monitor
            return get_monitor()
        except:
            return None
