import hashlib
from datetime import datetime
import json
import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.signal import Signal
from app.models.raw_document import RawDocument

logger = logging.getLogger(__name__)

class SignalBus:

    def __init__(self, db: AsyncSession):
        self.db = db

    def create_fingerprint(self, data: str) -> str:
        return hashlib.sha256(
            data.encode("utf-8")
        ).hexdigest()

    async def publish(self, raw_data: Dict[str, Any], signal_data: Dict[str, Any]) -> Signal:
        """
        Single public method.
        Saves the RawDocument (if not exists) and then saves the Signal.
        """
        # 1. Deduplicate/Archive RawDocument
        source_name = raw_data.get("source_name", "UNKNOWN")
        url = raw_data.get("url", "UNKNOWN")
        doc_hash = self.create_fingerprint(f"{source_name}:{url}")

        stmt = select(RawDocument).where(RawDocument.doc_hash == doc_hash)
        result = await self.db.execute(stmt)
        raw_doc = result.scalars().first()

        if not raw_doc:
            # Safely parse JSON if needed
            json_payload = None
            if raw_data.get("mime_type") == "application/json" and raw_data.get("payload"):
                try:
                    json_payload = json.loads(raw_data.get("payload"))
                except:
                    pass

            raw_doc = RawDocument(
                source_name=source_name,
                url=url,
                raw_html=raw_data.get("payload") if raw_data.get("mime_type") == "text/html" else None,
                rss_xml=raw_data.get("payload") if raw_data.get("mime_type") == "application/rss+xml" else None,
                json_payload=json_payload,
                headers=raw_data.get("headers"),
                etag=raw_data.get("etag"),
                last_modified=raw_data.get("last_modified"),
                response_time_ms=raw_data.get("response_time_ms"),
                response_size_bytes=raw_data.get("response_size_bytes"),
                connector_version=raw_data.get("connector_version"),
                feed_url=raw_data.get("feed_url"),
                doc_hash=doc_hash
            )
            self.db.add(raw_doc)
            await self.db.commit()
            await self.db.refresh(raw_doc)

        # 2. Save Signal
        signal_fingerprint = self.create_fingerprint(
            f"{signal_data.get('source_name')}:{signal_data.get('title')}:{signal_data.get('url')}"
        )
        
        signal = Signal(
            source_name=signal_data.get("source_name", source_name),
            title=signal_data.get("title", ""),
            summary=signal_data.get("summary", ""),
            url=signal_data.get("url", url),
            category=signal_data.get("category", ""),
            language=signal_data.get("language", "en"),
            reliability=signal_data.get("reliability", 50.0),
            importance=signal_data.get("importance", 50.0),
            freshness=signal_data.get("freshness", 5.0),
            created_at=datetime.utcnow(),
            raw_document_id=raw_doc.id
        )
        # Note: Added fingerprint deduplication logic on Signal in a real app if required
        # For MVP we just insert.

        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)

        return signal
