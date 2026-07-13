import httpx
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class AppleNewsroomConnector(BaseConnector):
    """
    Tier 1 Official Source: Apple Newsroom
    """
    RSS_URL = "https://www.apple.com/newsroom/rss-feed.rss"

    def __init__(self, signal_bus):
        self.bus = signal_bus
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"])

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "apple_newsroom",
            "name": "Apple Newsroom",
            "priority": 100,
            "official": True,
            "reliability": 40, # Max points for official source
            "country": "US",
            "category": "Apple",
            "schedule": "15m",
            "etag_support": True,
            "rate_limit": "No strict limit, but act politely",
            "expected_latency_ms": 400
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 3,
            "backoff_factor": 2.0,
            "circuit_breaker_enabled": True,
            "timeout_seconds": 20
        }

    async def discover(self) -> List[str]:
        # RSS feed is a single target
        return [self.RSS_URL]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[APPLE] Fetching {target}")
        response = await self.client.get(target)
        response.raise_for_status()
        
        return {
            "source_name": "Apple Newsroom",
            "url": target,
            "payload": response.text,
            "mime_type": "application/rss+xml",
            "headers": dict(response.headers),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "response_size_bytes": len(response.content),
            "connector_version": "1.1",
            "feed_url": target
        }

    async def archive(self, raw_data: Dict[str, Any]) -> int:
        return await self.bus.archive_raw(raw_data)

    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Extremely basic RSS parsing using BeautifulSoup
        soup = BeautifulSoup(raw_data["payload"], "xml")
        items = soup.find_all("item")
        
        signals = []
        for item in items:
            signals.append({
                "source_name": "Apple Newsroom",
                "title": item.title.text if item.title else "",
                "url": item.link.text if item.link else "",
                "summary": item.description.text if item.description else "",
                "category": "Apple",
                "reliability": 40,
                "freshness": 10
            })
        return signals

    async def publish(self, signal: Dict[str, Any], raw_doc_id: int) -> None:
        await self.bus.publish_signal(signal, raw_doc_id=raw_doc_id)

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get(self.RSS_URL)
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}

    async def execute(self) -> None:
        """Override execute to handle multiple signals returned by normalize"""
        targets = await self.discover()
        for target in targets:
            raw_data = await self.fetch(target)
            raw_doc_id = await self.archive(raw_data)
            
            signals = await self.normalize(raw_data)
            for signal in signals:
                await self.publish(signal, raw_doc_id)
