import httpx
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class RedditConnector(BaseConnector):
    """
    Tier 2 Source: Reddit Communities
    High volume, real-time user friction from subreddits.
    """
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"], follow_redirects=True)
        self.headers = {"User-Agent": "TechWithErikEngine/1.0"}

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "reddit",
            "name": "Reddit Communities",
            "priority": 80,
            "official": False,
            "reliability": 50,
            "importance": 90,
            "country": "US/Global",
            "category": "Community",
            "schedule": "30m",
            "etag_support": False,
            "rate_limit": "Reddit RSS rate limits apply",
            "expected_latency_ms": 1500
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 3,
            "backoff_factor": 2.0,
            "circuit_breaker_enabled": True,
            "timeout_seconds": 30
        }

    async def discover(self) -> List[str]:
        return [
            "https://www.reddit.com/r/apple/.rss?sort=hot",
            "https://www.reddit.com/r/samsung/.rss?sort=hot",
            "https://www.reddit.com/r/iphone/.rss?sort=hot",
            "https://www.reddit.com/r/Android/.rss?sort=hot"
        ]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[REDDIT] Fetching {target}")
        response = await self.client.get(target, headers=self.headers)
        response.raise_for_status()
        
        return {
            "source_name": "Reddit",
            "url": target,
            "payload": response.text,
            "mime_type": "application/rss+xml",
            "headers": dict(response.headers),
            "status_code": response.status_code,
            "feed_url": target
        }

    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(raw_data["payload"], "xml")
        entries = soup.find_all("entry")
        
        signals = []
        for entry in entries[:15]: 
            title = entry.find("title").text if entry.find("title") else "Unknown"
            link = entry.find("link")["href"] if entry.find("link") else raw_data["url"]
            
            signals.append({
                "source_name": "Reddit",
                "title": title.strip(),
                "url": link,
                "summary": "Reddit community post.",
                "category": "Friction",
                "reliability": 50,
                "importance": 75, 
                "freshness": 9,
                "language": "en"
            })
            
        return signals

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get("https://www.reddit.com/r/apple/.rss", headers=self.headers)
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}
