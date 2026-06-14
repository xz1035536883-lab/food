"""User model."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime

from ..database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), unique=True, nullable=False, index=True)
    nickname = Column(String(64), default="")
    avatar_url = Column(String(256), default="")
    daily_calorie_target = Column(Integer, default=2000)

    # Body profile
    gender = Column(String(8), default="")
    age = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "daily_calorie_target": self.daily_calorie_target,
            "gender": self.gender,
            "age": self.age,
            "height": self.height,
            "weight": self.weight,
            "target_weight": self.target_weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
