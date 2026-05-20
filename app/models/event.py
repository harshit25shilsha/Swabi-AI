from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserEvent(Base):
    __tablename__ = "user_events"

    event_id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, index=True)
    event_type      = Column(String(50))   # package_viewed, activity_viewed, search_performed
    package_id      = Column(Integer, nullable=True)
    activity_id     = Column(Integer, nullable=True)
    query_text      = Column(Text, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())