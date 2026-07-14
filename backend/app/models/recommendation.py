from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class HumanDecision(str, Enum):
    PENDING = "PENDING"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    POSTPONE = "POSTPONE"
    ARCHIVE = "ARCHIVE"

class Recommendation(Base):
    """
    The ultimate output of the MVP. 
    Answers: "What should Erik film today?"
    """
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    
    film_decision = Column(Boolean, nullable=False) # YES / NO from the AI
    topic = Column(String, nullable=False)
    
    confidence_percentage = Column(Float, nullable=False)
    trust_score = Column(Float, nullable=False) # e.g. 9.8
    
    reasoning = Column(Text, nullable=False)
    reasons_against = Column(Text, nullable=True) # Why Not? Missing evidence, risk if wrong.
    
    estimated_filming_min = Column(Integer, nullable=True)
    
    # Human Approval Layer
    erik_decision = Column(SQLEnum(HumanDecision), default=HumanDecision.PENDING, index=True)
    erik_notes = Column(Text, nullable=True) # E.g., "Too similar to last week's video"
    
    date_generated = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="recommendation")
