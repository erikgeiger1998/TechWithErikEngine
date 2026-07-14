import httpx
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class DNSCConnector(BaseConnector):
    """
    Tier 1 Official Source: DNSC (Directoratul Național de Securitate Cibernetică)
    High Priority - Romanian Security Alerts
    """
    # Using the alerts RSS/feed URL
    FEED_URL = "https://www.dnsc.ro/rss"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"], follow_redirects=True)

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "dnsc_alerts",
            "name": "DNSC Alerts",
            "priority": 100,
            "official": True,
            "reliability": 99, 
            "importance": 100, # Max importance for Romanian security
            "country": "RO",
            "category": "Security",
            "schedule": "30m",
            "etag_support": False,
            "rate_limit": "Be polite",
            "expected_latency_ms": 600
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 3,
            "backoff_factor": 2.0,
            "circuit_breaker_enabled": True,
            "timeout_seconds": 30
        }

    async def discover(self) -> List[str]:
        return [self.FEED_URL]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[DNSC] Fetching {target}")
        try:
            response = await self.client.get(target)
            response.raise_for_status()
            
            return {
                "source_name": "DNSC",
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
        except Exception as e:
            logger.error(f"[DNSC] Failed to fetch {target}: {str(e)}")
            raise



    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(raw_data["payload"], "xml")
        items = soup.find_all("item")
        
        signals = []
        for item in items:
            signals.append({
                "source_name": "DNSC",
                "title": item.title.text if item.title else "",
                "url": item.link.text if item.link else "",
                "summary": item.description.text if item.description else "",
                "category": "Security",
                "reliability": 99,
                "importance": 100,
                "freshness": 10,
                "language": "ro"
            })
        return signals

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get(self.FEED_URL)
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}

