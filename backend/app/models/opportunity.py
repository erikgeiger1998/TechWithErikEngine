from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class OpportunityStatus(str, Enum):
    NEW = "NEW"
    WATCHING = "WATCHING"
    READY = "READY"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    PUBLISHED = "PUBLISHED"

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, unique=True)
    
    status = Column(SQLEnum(OpportunityStatus), default=OpportunityStatus.NEW, index=True)
    
    # Explainability
    why = Column(Text, nullable=True)
    why_not = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    missing_evidence = Column(Text, nullable=True)
    risk_if_wrong = Column(Text, nullable=True)
    
    # Editorial ROI Components
    roi_impact = Column(Float, default=0.0)
    roi_trust = Column(Float, default=0.0)
    roi_demand = Column(Float, default=0.0)
    roi_production_ease = Column(Float, default=0.0)
    roi_total = Column(Float, default=0.0) # Impact * Trust * Demand * Production Ease
    
    # Opportunity Memory (Proprietary Dataset)
    is_published = Column(Boolean, default=False)
    production_time_min = Column(Integer, nullable=True)
    editing_time_min = Column(Integer, nullable=True)
    views = Column(Integer, nullable=True)
    avg_watch_time_sec = Column(Integer, nullable=True)
    retention_percent = Column(Float, nullable=True)
    shares = Column(Integer, nullable=True)
    saves = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    would_produce_again = Column(Boolean, nullable=True)
    best_hook = Column(Text, nullable=True)
    worst_mistake = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    problem = relationship("Problem", back_populates="opportunity")
    recommendation = relationship("Recommendation", back_populates="opportunity", uselist=False)
