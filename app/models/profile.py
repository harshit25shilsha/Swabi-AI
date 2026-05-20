from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profile"

    user_id         = Column(Integer, primary_key=True)
    place_scores    = Column(Text, default="{}")   # {"mountain":5, "beach":3}
    activity_scores = Column(Text, default="{}")   # {"hiking":4, "swimming":2}
    purpose_scores  = Column(Text, default="{}")   # {"adventure":6}
    season_scores   = Column(Text, default="{}")   # {"spring":3}
    budget_pref     = Column(String(50))
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())