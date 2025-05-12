from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from .db import Base
import datetime

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)            # "zoom" or "google_meet"
    meeting_id = Column(String, index=True)
    recording_url = Column(String)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    transcript_fetched = Column(Boolean, default=False)
    transcript_path = Column(String, nullable=True)
    summary = Column(String, nullable=True) # Stores the GPT-4o summary

    # Relationship to metrics
    # metrics = relationship("SummaryMetrics", back_populates="recording")

class SummaryMetrics(Base):
    __tablename__ = "summary_metrics"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
