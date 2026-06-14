"""Weight record router."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..schemas.weight_record import WeightRecordCreateReq
from ..services.weight_service import upsert_weight_record, get_weight_records, get_weight_summary
from ..utils.response import success, fail

router = APIRouter(prefix="/api/weight", tags=["体重记录"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id_from_header(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        return 0
    token = authorization[7:]
    from ..services.auth_service import get_current_user
    db = SessionLocal()
    try:
        user = get_current_user(db, token)
        return user.id if user else 0
    finally:
        db.close()


@router.post("")
def save_weight_record(
    req: WeightRecordCreateReq,
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    if not user_id:
        return fail(code=401, message="未登录")
    if req.weight < 20 or req.weight > 500:
        return fail(message="体重需在 20-500 kg 之间")
    record = upsert_weight_record(db, user_id, req)
    db.commit()
    db.refresh(record)
    return success(record.to_dict())


@router.get("")
def list_weight_records(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=90),
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    if not user_id:
        return fail(code=401, message="未登录")
    records = get_weight_records(db, user_id, date_from=date_from, date_to=date_to, limit=limit)
    return success({"records": [item.to_dict() for item in records]})


@router.get("/summary")
def weight_summary(
    days: int = Query(14, ge=1, le=90),
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    if not user_id:
        return fail(code=401, message="未登录")
    summary = get_weight_summary(db, user_id, days=days)
    return success(summary.model_dump())
