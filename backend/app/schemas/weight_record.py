"""Weight record schemas."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class WeightRecordCreateReq(BaseModel):
    weight: float
    record_date: date
    note: str = ""


class WeightRecordRsp(BaseModel):
    id: int
    user_id: int
    weight: float
    record_date: str
    note: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WeightRecordListRsp(BaseModel):
    records: list[WeightRecordRsp]


class WeightSummaryRsp(BaseModel):
    latest_weight: Optional[float] = None
    latest_date: Optional[str] = None
    first_weight: Optional[float] = None
    change_total: float = 0
    change_7d: float = 0
    records_count: int = 0
