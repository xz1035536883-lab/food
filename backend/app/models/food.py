"""Food nutrition model."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Numeric

from ..database import Base


class Food(Base):
    __tablename__ = "food"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, index=True)
    category = Column(String(32), nullable=False, default="其他")
    calories = Column(Numeric(8, 2), nullable=False, default=0)
    protein = Column(Numeric(6, 2), nullable=False, default=0)
    fat = Column(Numeric(6, 2), nullable=False, default=0)
    carbs = Column(Numeric(6, 2), nullable=False, default=0)
    fiber = Column(Numeric(6, 2), nullable=False, default=0)
    image_url = Column(String(256), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "calories": float(self.calories),
            "protein": float(self.protein),
            "fat": float(self.fat),
            "carbs": float(self.carbs),
            "fiber": float(self.fiber),
            "image_url": self.image_url,
        }
