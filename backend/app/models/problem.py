from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ARRAY, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ProblemState(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATING = "VALIDATING"
    HIGH_DEMAND = "HIGH_DEMAND"
    CONTENT_READY = "CONTENT_READY"
    COVERED = "COVERED"
    DORMANT = "DORMANT"
    SEASONAL_RETURN = "SEASONAL_RETURN"

class Problem(Base):
    """
    Problem Intelligence
    The permanent, central brain cell of the OS. Replaces the temporary 'Event'.
    """
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True) # e.g. "PHONE_OVERHEATING"
    aliases = Column(ARRAY(String), nullable=True) # e.g. ["iphone hot", "telefon fierbinte"]
    
    state = Column(SQLEnum(ProblemState), default=ProblemState.DISCOVERED, index=True)
    
    # Context & Scores
    # Context & Scores
    seasonality = Column(String, nullable=True) # e.g. "Summer"
    seasonality_multiplier = Column(Float, default=1.0) # Multiplier for time of year relevance
    severity = Column(Float, default=0.0) # e.g. 8.7
    visual_proof = Column(Boolean, default=False)
    evergreen_score = Column(Float, default=0.0) # 0-10 scale
    production_ease = Column(Float, default=7.0) # 1-10 scale
    
    # Monetization
    related_products = Column(ARRAY(String), nullable=True) # e.g. ["Cooling mounts", "Chargers"]
    sponsor_categories = Column(ARRAY(String), nullable=True) # e.g. ["VPN", "Hardware"]
    
    # Video History
    videos_published_dates = Column(ARRAY(String), nullable=True)
    can_publish_again = Column(String, nullable=True) # e.g. "Next summer"
    lessons_learned = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    signals = relationship("Signal", back_populates="problem")
    opportunity = relationship("Opportunity", back_populates="problem", uselist=False)
