from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class PackageCache(Base):
    __tablename__ ="package_cache"
    
    package_id = Column(Integer, primary_key=True)
    package_name = Column(String(500))
    country = Column(String(100))
    state = Column(String(100))
    no_of_days = Column(Integer)
    total_price = Column(Float)
    package_status = Column(String(20))
    modified_date = Column(String(50))
    raw_json = Column(Text)
    last_synced_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    

class PackageTags(Base):
    __tablename__ = "package_tags"
    
     
    package_id      = Column(Integer, primary_key=True)
    place_types     = Column(Text)    # JSON string ["mountain","valley"]
    activity_tags   = Column(Text)    # JSON string ["hiking","trekking"]
    trip_purpose    = Column(Text)    # JSON string ["adventure","solo"]
    season_tags     = Column(Text)    # JSON string ["spring","summer"]
    duration_type   = Column(String(50))   # short_trip / long_trip
    budget_category = Column(String(50))   # budget / mid_range / luxury
    tagged_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())