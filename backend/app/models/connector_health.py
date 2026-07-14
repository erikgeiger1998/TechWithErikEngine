from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database.base import Base

class ConnectorStatus(str, PyEnum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    FAILED = "FAILED"
    DISABLED = "DISABLED"

class ConnectorHealth(Base):
    __tablename__ = "connector_health"

    id = Column(Integer, primary_key=True, index=True)
    connector_name = Column(String, index=True, nullable=False, unique=True)
    
    status = Column(SQLEnum(ConnectorStatus), default=ConnectorStatus.DISABLED)
    
    last_run = Column(DateTime(timezone=True), nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_failure = Column(DateTime(timezone=True), nullable=True)
    
    http_status = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)
    items_processed = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
