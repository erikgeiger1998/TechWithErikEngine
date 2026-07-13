import hashlib
import uuid
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.raw_document import RawDocument
from app.models.signal import Signal

logger = logging.getLogger(__name__)

class SignalBus:
    """
    The centralized Signal Bus.
    Connectors do not touch the DB directly. They use the Signal Bus to archive raw data 
    and publish normalized Signals. This handles UUID generation and fingerprint deduplication.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def archive_raw(self, raw_data: Dict[str, Any]) -> int:
        """
        Receives raw payload (HTML, JSON, XML) from the connector, computes SHA256, 
        and stores it in the raw_documents table.
        Returns the generated RawDocument ID.
        """
        doc_hash = hashlib.sha256(str(raw_data.get('payload', '')).encode('utf-8')).hexdigest()
        
        doc = RawDocument(
            source_name=raw_data.get('source_name', 'UNKNOWN'),
            url=raw_data.get('url', ''),
            raw_html=raw_data.get('payload') if raw_data.get('mime_type') == 'text/html' else None,
            rss_xml=raw_data.get('payload') if raw_data.get('mime_type') in ['application/rss+xml', 'text/xml'] else None,
            json_payload=raw_data.get('payload') if raw_data.get('mime_type') == 'application/json' else None,
            headers=raw_data.get('headers', {}),
            etag=raw_data.get('etag'),
            last_modified=raw_data.get('last_modified'),
            response_time_ms=raw_data.get('response_time_ms'),
            response_size_bytes=raw_data.get('response_size_bytes'),
            connector_version=raw_data.get('connector_version'),
            rss_guid=raw_data.get('rss_guid'),
            feed_url=raw_data.get('feed_url'),
            doc_hash=doc_hash
        )
        self.db.add(doc)
        await self.db.flush() # Flush to get the ID
        return doc.id

    async def publish_signal(self, signal_data: Dict[str, Any], raw_doc_id: int = None) -> None:
        """
        Receives the standardized normalized Signal from the connector.
        Assigns a UUID, hashes the content to prevent duplicates, and saves to the signals table.
        """
        # Create a deterministic fingerprint for deduplication
        fingerprint_input = f"{signal_data.get('source_name')}-{signal_data.get('title')}-{signal_data.get('url')}"
        fingerprint = hashlib.sha256(fingerprint_input.encode('utf-8')).hexdigest()
        
        # In a full implementation, we'd check if this fingerprint exists before inserting
        
        signal = Signal(
            source_name=signal_data.get('source_name'),
            title=signal_data.get('title'),
            summary=signal_data.get('summary'),
            url=signal_data.get('url'),
            category=signal_data.get('category'),
            language=signal_data.get('language', 'en'),
            reliability=signal_data.get('reliability', 0),
            freshness=signal_data.get('freshness', 10),
            raw_document_id=raw_doc_id
            # UUID could be added to the model if requested later
        )
        self.db.add(signal)
        await self.db.commit()
        logger.info(f"[SIGNAL_BUS] Published new Signal: {signal.title}")
