"""Diet record CRUD router."""
from datetime import date

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.diet_record import DietRecord
from ..schemas.diet_record import DietRecordCreateReq
from ..services.diet_service import create_record, get_records_by_date, get_daily_summary
from ..utils.response import success, fail

router = APIRouter(prefix="/api/record", tags=["饮食记录"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id_from_header(authorization: str = Header(None)) -> int:
    """Extract user_id from Bearer token."""
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
def add_record(
    req: DietRecordCreateReq,
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Create a new diet record."""
    if not user_id:
        return fail(code=401, message="未登录")
    record = create_record(db, user_id, req)
    db.commit()
    return success(record.to_dict())


@router.get("")
def list_records(
    record_date: date,
    meal_type: str = None,
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Get diet records for a date."""
    if not user_id:
        return fail(code=401, message="未登录")
    records = get_records_by_date(db, user_id, record_date, meal_type)
    total = sum(float(r.calories or 0) for r in records)
    return success({
        "records": [r.to_dict() for r in records],
        "total_calories": round(total, 2),
    })


@router.get("/summary")
def daily_summary(
    record_date: date,
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Get daily calorie summary."""
    if not user_id:
        return fail(code=401, message="未登录")
    from ..models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    target = user.daily_calorie_target if user else 2000
    summary = get_daily_summary(db, user_id, record_date, target)
    return success(summary.model_dump())


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    user_id: int = Depends(get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Delete a diet record."""
    if not user_id:
        return fail(code=401, message="未登录")
    record = db.query(DietRecord).filter(
        DietRecord.id == record_id,
        DietRecord.user_id == user_id,
    ).first()
    if not record:
        return fail(message="记录不存在")
    db.delete(record)
    db.commit()
    return success({"deleted": True})
