from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    user_id  = Column(Integer, primary_key=True)
    activity_types = Column(Text, default="[]")  # ["hiking","Food tours"]
    place_types = Column(Text, default="[]")     # ["mountain","beach"]
    season = Column(Text, default="[]")          # ["summer","winter"]
    trip_purposes = Column(Text, default="[]")   #["solo trip","Honeymoon"]
    trip_duration = Column(Text, default="[]")   # ["short_trip","long_trip"]
    countries = Column(Text, default="[]")        # ["India","Nepal"]
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    