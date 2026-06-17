from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    skill_rating = Column(Integer, default=1000)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now())

    hands = relationship("Hand", back_populates="user")
