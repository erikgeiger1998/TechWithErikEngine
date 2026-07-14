import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.signal_bus import SignalBus
from app.connectors.apple_newsroom import AppleNewsroomConnector
from app.connectors.apple_support import AppleSupportConnector
from app.connectors.dnsc import DNSCConnector
from app.connectors.google_autocomplete import GoogleAutocompleteConnector
from app.connectors.google_trends import GoogleTrendsRomaniaConnector

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

    async def fetch(self, source: str):
        """
        Fetches from a specific source, or 'all' for all registered sources.
        """
        targets = []
        if source == "all":
            targets = list(self.connectors.keys())
        else:
            if source not in self.connectors:
                logger.error(f"Unknown connector source: {source}")
                return
            targets = [source]

        for target_key in targets:
            connector = self.connectors[target_key]
            try:
                logger.info(f"Starting ingestion for {target_key}...")
                urls_to_fetch = await connector.discover()
                
                for url in urls_to_fetch:
                    try:
                        raw_data = await connector.fetch(url)
                        signals = await connector.normalize(raw_data)
                        
                        for signal_data in signals:
                            await self.bus.publish(raw_data, signal_data)
                            
                    except Exception as e:
                        logger.error(f"Failed to process URL {url} for {target_key}: {e}")
            except Exception as e:
                logger.error(f"Failed discovery for {target_key}: {e}")
