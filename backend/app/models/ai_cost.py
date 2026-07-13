from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database.base import Base

class AICostTracker(Base):
    __tablename__ = "ai_costs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True, nullable=False)
    
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    cost_usd = Column(Float, nullable=False)
    
    latency_ms = Column(Integer, nullable=True)
    task_type = Column(String, nullable=True) # e.g. "Opportunity Scoring", "Explainability"
    
    prompt_snippet = Column(Text, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
