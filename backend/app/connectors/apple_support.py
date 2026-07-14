import httpx
import logging
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class AppleSupportConnector(BaseConnector):
    """
    Tier 1 Official Source: Apple Support
    Massive Priority - Canonical user friction guidance and official solutions.
    """
    # Using the primary US English sitemap for discovery of new/updated support articles
    SITEMAP_URL = "https://support.apple.com/sitemap.xml"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"])

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "apple_support",
            "name": "Apple Support",
            "priority": 100,
            "official": True,
            "reliability": 100, # Max reliability for official solutions
            "importance": 100, # Max importance for resolving user friction
            "country": "US",
            "category": "Support",
            "schedule": "120m", # Sitemaps don't need 15m polling
            "etag_support": True,
            "rate_limit": "Be polite to Apple infrastructure",
            "expected_latency_ms": 1200
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 4,
            "backoff_factor": 3.0,
            "circuit_breaker_enabled": True,
            "timeout_seconds": 60
        }

    async def discover(self) -> List[str]:
        """
        Parses the main sitemap to find recent article sitemap indices.
        In a full implementation, we'd parse the child sitemaps and return specific HTxxxx article URLs.
        For MVP ingestion, we'll return a static list of known high-friction articles.
        """
        # MVP: High-friction canonical documents
        return [
            "https://support.apple.com/en-us/HT208086", # Bluetooth/Wi-Fi in Control Center
            "https://support.apple.com/en-us/HT201678", # iPhone Battery and Performance
            "https://support.apple.com/en-us/HT201569"  # If your iPhone gets too hot or too cold
        ]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[APPLE_SUPPORT] Fetching {target}")
        response = await self.client.get(target)
        response.raise_for_status()
        
        return {
            "source_name": "Apple Support",
            "url": target,
            "payload": response.text,
            "mime_type": "text/html",
            "headers": dict(response.headers),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "response_size_bytes": len(response.content),
            "connector_version": "1.0",
            "feed_url": target
        }



    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(raw_data["payload"], "html.parser")
        
        title_tag = soup.find("title")
        title = title_tag.text if title_tag else "Unknown Support Article"
        
        # Extremely basic extraction of meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        summary = meta_desc["content"] if meta_desc else "No summary available."
        
        signals = [{
            "source_name": "Apple Support",
            "title": title.strip(),
            "url": raw_data["url"],
            "summary": summary.strip(),
            "category": "Support",
            "reliability": 100,
            "importance": 100,
            "freshness": 5, # Support docs are highly evergreen, freshness is less spiky
            "language": "en"
        }]
        
        return signals

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get("https://support.apple.com/en-us/HT201678")
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}

