from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class PublishedVideo(Base):
    """
    Tracks the historical performance of videos that Erik has actually published.
    This creates the proprietary feedback loop for the OS.
    """
    __tablename__ = "published_videos"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True, index=True)
    
    video_url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    
    # Public Performance Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Advanced metrics (can be populated manually or via future integrations)
    retention_rate = Column(Float, nullable=True) 
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    problem = relationship("Problem", back_populates="videos")
