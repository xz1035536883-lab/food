"""Daily weight record model."""
from datetime import date, datetime

from sqlalchemy import Column, Integer, Float, DateTime, Date, ForeignKey, String

from ..database import Base


class WeightRecord(Base):
    __tablename__ = "weight_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    record_date = Column(Date, nullable=False, default=date.today, index=True)
    note = Column(String(128), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "weight": self.weight,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "note": self.note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
