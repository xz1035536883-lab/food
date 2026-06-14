"""Diet record schemas."""
from typing import Optional
from datetime import date
from pydantic import BaseModel


class DietRecordCreateReq(BaseModel):
    food_id: int
    food_name: str
    image_url: str = ""
    weight: int = 100
    calories: Optional[float] = None
    meal_type: str = "snack"
    record_date: date


class DietRecordUpdateReq(BaseModel):
    weight: Optional[int] = None
    meal_type: Optional[str] = None


class DietRecordRsp(BaseModel):
    id: int
    user_id: int
    food_id: int
    food_name: str
    image_url: str
    weight: int
    calories: float
    meal_type: str
    record_date: str
    created_at: str


class DietRecordListRsp(BaseModel):
    records: list[DietRecordRsp]
    total_calories: float


class DailySummaryRsp(BaseModel):
    total: float
    target: int
    breakfast: float
    lunch: float
    dinner: float
    snack: float
