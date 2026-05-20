from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserCache(Base):
    __tablename__ = "users_cache"
    
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(200))
    last_name = Column(String(200))
    country = Column(String(100))
    state = Column(String(100))
    gender = Column(String(20))
    last_synced_at = Column(DateTime, server_default=func.now(), onupdate=func.now())