from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class BookingHistory(Base):
    __tablename__ = "booking_history"
    
    booking_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    package_id = Column(Integer, index=True)
    booking_status = Column(String(50))
    booking_date = Column(String(50))
    amount_paid = Column(Float)
    num_members = Column(Integer)
    synced_at = Column(DateTime,server_default=func.now())
    