import httpx
import logging
import json
from typing import Dict, Any, List
from app.core.connector import BaseConnector

logger = logging.getLogger(__name__)

class GoogleAutocompleteConnector(BaseConnector):
    """
    Tier 1 Human Friction Source: Google Autocomplete
    Highly predictive source. Fetches exact human pain points (e.g. 'iphone se incinge').
    """
    # Google Autocomplete API for Chrome/Firefox, returning JSON
    BASE_URL = "http://suggestqueries.google.com/complete/search?client=chrome&hl=ro&gl=ro&q="

    def __init__(self, signal_bus):
        self.bus = signal_bus
        self.client = httpx.AsyncClient(timeout=self.retry_policy()["timeout_seconds"])

    async def metadata(self) -> Dict[str, Any]:
        return {
            "id": "google_autocomplete_ro",
            "name": "Google Autocomplete",
            "priority": 90,
            "official": False,
            "reliability": 0, # Not "Is it true?" but "Are people asking?"
            "importance": 90, # Huge predictive importance
            "country": "RO",
            "category": "Demand",
            "schedule": "60m",
            "etag_support": False,
            "rate_limit": "Very Strict - IP block possible if abused",
            "expected_latency_ms": 300
        }

    def retry_policy(self) -> Dict[str, Any]:
        return {
            "max_retries": 2,
            "backoff_factor": 5.0, # Slow down heavily if rejected
            "circuit_breaker_enabled": True,
            "timeout_seconds": 15
        }

    async def discover(self) -> List[str]:
        # A list of root queries to test human friction against
        seed_queries = ["iphone", "baterie iphone", "iphone nu", "whatsapp", "android", "telefonul se"]
        return [f"{self.BASE_URL}{httpx.utils.quote(q)}" for q in seed_queries]

    async def fetch(self, target: str) -> Dict[str, Any]:
        logger.info(f"[AUTOCOMPLETE] Fetching {target}")
        response = await self.client.get(target)
        response.raise_for_status()
        
        return {
            "source_name": "Google Autocomplete",
            "url": target,
            "payload": response.text,
            "mime_type": "application/json",
            "headers": dict(response.headers),
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "response_size_bytes": len(response.content),
            "connector_version": "1.0",
            "feed_url": target
        }

    async def archive(self, raw_data: Dict[str, Any]) -> int:
        return await self.bus.archive_raw(raw_data)

    async def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Example JSON response: ["iphone", ["iphone 15", "iphone 13", "iphone se incinge"], ...]
        try:
            data = json.loads(raw_data["payload"])
            root_query = data[0]
            suggestions = data[1] if len(data) > 1 else []
        except json.JSONDecodeError:
            logger.error("[AUTOCOMPLETE] Failed to parse JSON response")
            return []
            
        signals = []
        for i, suggestion in enumerate(suggestions):
            # The higher the suggestion, the higher the volume weight
            volume_weight = len(suggestions) - i 
            
            signals.append({
                "source_name": "Google Autocomplete",
                "title": f"Human Query: {suggestion}",
                "url": raw_data["url"], # Not a real clickable URL, but tracks the root query
                "summary": suggestion,
                "category": "Friction",
                "reliability": 0,
                "importance": 90,
                "freshness": 10,
                "language": "ro",
                
                # HumanSignal specific mappings for the Problem Clustering Engine later
                "raw_query": suggestion,
                "normalized_problem": suggestion.upper().replace(" ", "_"), # Temp normalization
                "search_volume": "high" if i < 3 else "medium"
            })
        return signals

    async def publish(self, signal: Dict[str, Any], raw_doc_id: int) -> None:
        await self.bus.publish_signal(signal, raw_doc_id=raw_doc_id)

    async def health(self) -> Dict[str, Any]:
        try:
            res = await self.client.get(self.BASE_URL + "test")
            if res.status_code == 200:
                return {"status": "Healthy", "latency_ms": res.elapsed.total_seconds() * 1000, "errors": 0}
            elif res.status_code == 429:
                return {"status": "Warning", "error": "Rate limited by Google"}
        except Exception as e:
            return {"status": "Unhealthy", "error": str(e)}
        return {"status": "Warning", "error": "Unknown"}

    async def execute(self) -> None:
        targets = await self.discover()
        for target in targets:
            try:
                raw_data = await self.fetch(target)
                raw_doc_id = await self.archive(raw_data)
                
                signals = await self.normalize(raw_data)
                for signal in signals:
                    await self.publish(signal, raw_doc_id)
            except Exception as e:
                logger.error(f"[AUTOCOMPLETE] Failed processing {target}: {str(e)}")
