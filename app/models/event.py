from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class UserEvent(Base):
    __tablename__ = "user_events"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    event_id    = Column(String(100), unique=True, nullable=True)  # UUID from view events
    user_id     = Column(Integer, index=True)
    event_type  = Column(String(50))   # package_viewed / search_performed
    package_id  = Column(Integer, nullable=True)
    activity_ids = Column(Text, nullable=True)   # JSON list
    country      = Column(String(100), nullable=True)
    state       = Column(String(100), nullable=True)
    search_date = Column(String(50), nullable=True)  # date user wants to travel
    created_at  = Column(DateTime)
    synced_at   = Column(DateTime, server_default=func.now())
    scored      = Column(Boolean, default=False)  # Whether this event has been processed for scoring