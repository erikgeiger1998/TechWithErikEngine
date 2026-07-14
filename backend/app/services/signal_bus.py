import hashlib
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal


class SignalBus:

    def __init__(self, db: AsyncSession):
        self.db = db


    def create_fingerprint(self, data: str) -> str:
        return hashlib.sha256(
            data.encode("utf-8")
        ).hexdigest()


    async def publish(
        self,
        *,
        title: str,
        url: str,
        source_name: str,
        raw_content: str,
        signal_type: str = "GENERAL"
    ):

        fingerprint = self.create_fingerprint(
            f"{source_name}:{title}:{url}"
        )

        signal = Signal(
            title=title,
            url=url,
            source_name=source_name,
            raw_content=raw_content,
            fingerprint=fingerprint,
            signal_type=signal_type,
            created_at=datetime.utcnow()
        )

        self.db.add(signal)

        await self.db.commit()

        await self.db.refresh(signal)

        return signal
