from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from app.database.base import Base

class RawDocument(Base):
    __tablename__ = "raw_documents"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, index=True, nullable=False)
    url = Column(String, index=True, nullable=False)
    
    raw_html = Column(Text, nullable=True)
    rss_xml = Column(Text, nullable=True)
    json_payload = Column(JSON, nullable=True)
    
    # Advanced Data Telemetry
    headers = Column(JSON, nullable=True)
    etag = Column(String, nullable=True)
    last_modified = Column(String, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    connector_version = Column(String, nullable=True)
    
    rss_guid = Column(String, nullable=True)
    feed_url = Column(String, nullable=True)
    
    doc_hash = Column(String, index=True, nullable=False) # Fingerprint deduplication
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
