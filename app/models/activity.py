from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class ActivityCache(Base):
    __tablename__ = "activities_cache"
    
    activity_id = Column(Integer, primary_key=True)
    activity_name = Column(String(500))
    description = Column(String(2000))
    category = Column(String(200))
    best_time = Column(String(100))
    country = Column(String(100))
    state = Column(String(100))
    price = Column(Float)
    modified_date = Column(String(50))
    last_synced_at = Column(DateTime, server_default=func.now(),onupdate=func.now())