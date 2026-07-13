from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database.base import Base

class ConnectorType(str, Enum):
    OFFICIAL = "OFFICIAL"
    TREND = "TREND"
    COMMUNITY = "COMMUNITY"
    MEDIA = "MEDIA"

class SourceProfile(Base):
    __tablename__ = "source_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    connector_type = Column(SQLEnum(ConnectorType), default=ConnectorType.MEDIA, index=True)
    
    reliability = Column(Float, nullable=False) # "Is it true?"
    importance = Column(Float, nullable=False, default=50.0) # "How much should this influence decisions?"
    
    romanian_relevance = Column(Float, nullable=False)
    is_official = Column(Boolean, default=False)
    
    update_frequency = Column(String, nullable=True)
    expected_latency = Column(String, nullable=True)
    category = Column(String, nullable=True)
    language = Column(String, default="en")
    api_available = Column(Boolean, default=False)
    rate_limits = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
