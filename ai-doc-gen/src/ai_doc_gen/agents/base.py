"""
Base classes and interfaces for AI agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class AgentBase(ABC):
    """Abstract base class for all agents."""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the agent's main logic."""
        pass

    @abstractmethod
    def report(self) -> Dict[str, Any]:
        """Return a summary or report of the agent's actions/results."""
        pass 