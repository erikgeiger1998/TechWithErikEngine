from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String, index=True, nullable=False)
    category = Column(String, nullable=True)
    language = Column(String, default="en")
    
    reliability = Column(Float, nullable=False) # From Source Profile ("Is it true?")
    importance = Column(Float, nullable=False, default=50.0) # From Source Profile ("Influence?")
    freshness = Column(Float, nullable=False)   # Calculated by connector/bus
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    raw_document_id = Column(Integer, ForeignKey("raw_documents.id"), nullable=True)
    raw_document = relationship("RawDocument")
    
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)
    problem = relationship("Problem", back_populates="signals")
