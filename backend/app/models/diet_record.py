"""Diet record model."""
from datetime import datetime, date

from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey

from ..database import Base


class DietRecord(Base):
    __tablename__ = "diet_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    food_id = Column(Integer, ForeignKey("food.id"), nullable=False)
    food_name = Column(String(64), nullable=False)
    image_url = Column(String(256), default="")
    weight = Column(Integer, nullable=False, default=100)
    calories = Column(Numeric(8, 2), nullable=False, default=0)
    meal_type = Column(String(16), nullable=False, default="snack")
    record_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "food_id": self.food_id,
            "food_name": self.food_name,
            "image_url": self.image_url,
            "weight": self.weight,
            "calories": float(self.calories),
            "meal_type": self.meal_type,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
