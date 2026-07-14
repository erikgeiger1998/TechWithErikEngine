import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.services.signal_bus import SignalBus
from app.services.clustering import ProblemClusteringEngine
from app.connectors.apple_newsroom import AppleNewsroomConnector
from app.connectors.apple_support import AppleSupportConnector
from app.connectors.dnsc import DNSCConnector
from app.connectors.google_autocomplete import GoogleAutocompleteConnector
from app.connectors.google_trends import GoogleTrendsRomaniaConnector
from app.models.connector_health import ConnectorHealth, ConnectorStatus

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bus = SignalBus(db)
        
        # Instantiate connectors
        self.connectors = {
            "apple": AppleNewsroomConnector(),
            "apple_support": AppleSupportConnector(),
            "dnsc": DNSCConnector(),
            "autocomplete": GoogleAutocompleteConnector()
            # "trends": GoogleTrendsRomaniaConnector() # Temporarily disabled
        }

    async def _update_health(self, connector_name: str, status: ConnectorStatus, latency: float, items: int, duplicates: int, error_msg: str = None, http_status: str = None):
        stmt = select(ConnectorHealth).where(ConnectorHealth.connector_name == connector_name)
        result = await self.db.execute(stmt)
        health_record = result.scalars().first()
        
        now = datetime.now(timezone.utc)
        
        if not health_record:
            health_record = ConnectorHealth(connector_name=connector_name)
            self.db.add(health_record)
            
        health_record.last_run = now
        health_record.status = status
        health_record.latency_ms = latency
        health_record.items_processed = items
        health_record.duplicates = duplicates
        health_record.error_message = error_msg
        
        if http_status:
            health_record.http_status = http_status
            
        if status == ConnectorStatus.HEALTHY:
            health_record.last_success = now
        elif status == ConnectorStatus.FAILED:
            health_record.last_failure = now
            
        await self.db.commit()

    async def fetch(self, source: str) -> Dict[str, Any]:
        """
        Fetches from a specific source, or 'all' for all registered sources.
        Returns a summary dictionary of execution metrics.
        """
        targets = []
        if source == "all":
            targets = list(self.connectors.keys())
        else:
            if source not in self.connectors:
                logger.error(f"Unknown connector source: {source}")
                return {"error": f"Unknown connector {source}"}
            targets = [source]

        summary = {
            "processed": 0,
            "healthy": 0,
            "warnings": 0,
            "failures": 0,
            "details": {}
        }
        
        start_time = time.time()

        for target_key in targets:
            connector = self.connectors[target_key]
            connector_start = time.time()
            items_processed = 0
            duplicates = 0
            status = ConnectorStatus.HEALTHY
            error_msg = None
            http_status = None
            
            try:
                logger.info(f"Starting ingestion for {target_key}...")
                urls_to_fetch = await connector.discover()
                
                for url in urls_to_fetch:
                    try:
                        raw_data = await connector.fetch(url)
                        
                        if "headers" in raw_data and "status_code" in raw_data:
                            http_status = str(raw_data.get("status_code", 200))
                        else:
                            http_status = "200" # Assume 200 if fetch succeeds
                            
                        signals = await connector.normalize(raw_data)
                        
                        for signal_data in signals:
                            items_processed += 1
                            signal, is_duplicate = await self.bus.publish(raw_data, signal_data)
                            
                            # Attach signal to canonical problem
                            await ProblemClusteringEngine.attach_signal(self.db, signal)
                            
                            if is_duplicate:
                                duplicates += 1
                                
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Failed to process URL {url} for {target_key}: {e}")
                        
                        # Catch specific 403 Forbidden
                        if "403" in error_msg:
                            status = ConnectorStatus.WARNING
                            http_status = "403"
                        else:
                            status = ConnectorStatus.FAILED
                            
                # If we had a warning status during URL fetch but not a hard failure, we keep warning
                
            except Exception as e:
                error_msg = str(e)
                status = ConnectorStatus.FAILED
                logger.error(f"Failed discovery for {target_key}: {e}")
                
            latency_ms = (time.time() - connector_start) * 1000
            
            await self.update_connector_status(target_key, status, latency_ms, items_processed, duplicates, error_msg, http_status)
            
            # Update summary
            if status == ConnectorStatus.HEALTHY:
                summary["healthy"] += 1
            elif status == ConnectorStatus.WARNING:
                summary["warnings"] += 1
            else:
                summary["failures"] += 1
                
            summary["processed"] += items_processed
            summary["details"][target_key] = {
                "status": status.value,
                "items": items_processed,
                "error": error_msg
            }
            
        summary["duration_s"] = time.time() - start_time
        return summary
        
    async def update_connector_status(self, target_key: str, status: ConnectorStatus, latency: float, items: int, duplicates: int, error_msg: str, http_status: str):
        await self._update_health(target_key, status, latency, items, duplicates, error_msg, http_status)
