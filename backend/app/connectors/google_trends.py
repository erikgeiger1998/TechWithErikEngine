import httpx
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class GoogleTrendsRomaniaConnector(BaseConnector):
    """
    Tier 1 Trend Source: Google Trends (Romania)
    High Priority - Maps human demand spikes instantly.
    """
    # Daily trending searches RSS feed for Romania
    RSS_URL = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=RO"

    def __init__(self, signal_bus):
        self.bus = signal_bus
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"])

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "google_trends_ro",
            "name": "Google Trends Romania",
            "priority": 95,
            "official": False,
            "reliability": 0, # Reliability is N/A for Trends ("Is it true?" doesn't apply to a search query)
            "importance": 95, # Very high importance for demand detection
            "country": "RO",
            "category": "Demand",
            "schedule": "60m",
            "etag_support": False,
            "rate_limit": "Strict - Be very polite",
            "expected_latency_ms": 500
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 3,
            "backoff_factor": 2.5,
            "circuit_breaker_enabled": True,
            "timeout_seconds": 30
        }

    async def discover(self) -> List[str]:
        return [self.RSS_URL]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[TRENDS] Fetching {target}")
        response = await self.client.get(target)
        response.raise_for_status()
        
        return {
            "source_name": "Google Trends RO",
            "url": target,
            "payload": response.text,
            "mime_type": "application/rss+xml",
            "headers": dict(response.headers),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "response_size_bytes": len(response.content),
            "connector_version": "1.0",
            "feed_url": target
        }

    async def archive(self, raw_data: Dict[str, Any]) -> int:
        return await self.bus.archive_raw(raw_data)

    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(raw_data["payload"], "xml")
        items = soup.find_all("item")
        
        signals = []
        for item in items:
            # Google Trends RSS typically includes <ht:approx_traffic> and <ht:news_item> elements
            approx_traffic = item.find("ht:approx_traffic")
            traffic_text = approx_traffic.text if approx_traffic else "0"
            
            signals.append({
                "source_name": "Google Trends RO",
                "title": item.title.text if item.title else "",
                "url": item.link.text if item.link else "",
                "summary": f"Approximate Traffic: {traffic_text}",
                "category": "Demand",
                "reliability": 0,
                "importance": 95,
                "freshness": 10,
                "language": "ro"
            })
        return signals

    async def publish(self, signal: Dict[str, Any], raw_doc_id: int) -> None:
        await self.bus.publish_signal(signal, raw_doc_id=raw_doc_id)

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get(self.RSS_URL)
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
            elif res.status_code == 429:
                return {"status": "Warning", "error": "Rate limit nearly exhausted"}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}

    async def execute(self) -> None:
        targets = await self.discover()
        for target in targets:
            raw_data = await self.fetch(target)
            raw_doc_id = await self.archive(raw_data)
            
            signals = await self.normalize(raw_data)
            for signal in signals:
                await self.publish(signal, raw_doc_id)
