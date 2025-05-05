from sqlalchemy import Column, Integer, String, DateTime, Boolean
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
