from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """
    The Base Connector SDK.
    Every connector MUST inherit from this class and implement its methods.
    Connectors NEVER write to the database directly. They publish Signals to the Signal Bus.
    """

    @abstractmethod
    async def metadata(self) -> Dict[str, Any]:
        """
        Returns connector metadata.
        Expected format:
        {
            "id": "apple_newsroom",
            "priority": 10,
            "official": True,
            "reliability": 100,
            "country": "US",
            "category": "Apple",
            "schedule": "15m",
            "timeout_seconds": 20,
            "etag_support": True,
            "rate_limit": "100/hour",
            "expected_latency_ms": 300
        }
        """
        pass

    @abstractmethod
    def retry_policy(self) -> Dict[str, Any]:
        """
        Defines the resilience strategy.
        Expected format:
        {
            "max_retries": 3,
            "backoff_factor": 2.0,
            "circuit_breaker_enabled": True
        }
        """
        pass

    @abstractmethod
    async def discover(self) -> List[str]:
        """
        Identify URLs or IDs that need to be fetched.
        Returns a list of target URLs/identifiers.
        """
        pass

    @abstractmethod
    async def fetch(self, target: str) -> Dict[str, Any]:
        """
        Fetch the raw data from the target.
        Returns a dictionary containing the raw payload, headers, status codes, etc.
        """
        pass

    @abstractmethod
    async def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the raw data into a standard Signal format.
        """
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """
        Returns the current health status of the connector.
        e.g., {"status": "Healthy", "latency": 231, "errors": 0}
        """
        pass
