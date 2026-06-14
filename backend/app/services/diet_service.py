"""Diet record service."""
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.diet_record import DietRecord
from ..models.food import Food
from ..schemas.diet_record import (
    DietRecordCreateReq,
    DailySummaryRsp,
)


def create_record(db: Session, user_id: int, req: DietRecordCreateReq) -> DietRecord:
    """Create a diet record with calorie calculation."""
    # Calculate calories from food DB
    food = db.query(Food).filter(Food.id == req.food_id).first()
    if food:
        ratio = req.weight / 100.0
        calories = round(float(food.calories) * ratio, 2)
    elif req.calories is not None:
        calories = round(float(req.calories), 2)
    else:
        calories = 0

    record = DietRecord(
        user_id=user_id,
        food_id=req.food_id,
        food_name=req.food_name,
        image_url=req.image_url,
        weight=req.weight,
        calories=calories,
        meal_type=req.meal_type,
        record_date=req.record_date,
    )
    db.add(record)
    db.flush()
    return record


def get_records_by_date(
    db: Session, user_id: int, record_date: date, meal_type: str = None
) -> list[DietRecord]:
    """Get diet records for a specific date, optionally filtered by meal type."""
    query = db.query(DietRecord).filter(
        DietRecord.user_id == user_id,
        DietRecord.record_date == record_date,
    )
    if meal_type:
        query = query.filter(DietRecord.meal_type == meal_type)
    return query.order_by(DietRecord.created_at.desc()).all()


def get_daily_summary(db: Session, user_id: int, record_date: date, target: int) -> DailySummaryRsp:
    """Get daily calorie summary grouped by meal type."""
    records = db.query(DietRecord).filter(
        DietRecord.user_id == user_id,
        DietRecord.record_date == record_date,
    ).all()

    summary = {"breakfast": 0.0, "lunch": 0.0, "dinner": 0.0, "snack": 0.0}
    total = 0.0

    for r in records:
        cal = float(r.calories) if r.calories else 0
        total += cal
        if r.meal_type in summary:
            summary[r.meal_type] += cal

    return DailySummaryRsp(
        total=round(total, 2),
        target=target,
        breakfast=round(summary["breakfast"], 2),
        lunch=round(summary["lunch"], 2),
        dinner=round(summary["dinner"], 2),
        snack=round(summary["snack"], 2),
    )
