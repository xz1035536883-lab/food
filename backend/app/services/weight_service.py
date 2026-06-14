"""Weight record service."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..models.user import User
from ..models.weight_record import WeightRecord
from ..schemas.weight_record import WeightRecordCreateReq, WeightSummaryRsp


def upsert_weight_record(db: Session, user_id: int, req: WeightRecordCreateReq) -> WeightRecord:
    """Create or update a user's weight record for a date."""
    record = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id,
        WeightRecord.record_date == req.record_date,
    ).first()

    if record:
        record.weight = req.weight
        record.note = req.note
    else:
        record = WeightRecord(
            user_id=user_id,
            weight=req.weight,
            record_date=req.record_date,
            note=req.note,
        )
        db.add(record)
        db.flush()

    latest_record = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id,
    ).order_by(WeightRecord.record_date.desc(), WeightRecord.updated_at.desc()).first()

    if latest_record and latest_record.record_date <= req.record_date:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.weight = req.weight

    return record


def get_weight_records(
    db: Session,
    user_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: Optional[int] = None,
) -> list[WeightRecord]:
    query = db.query(WeightRecord).filter(WeightRecord.user_id == user_id)
    if date_from:
        query = query.filter(WeightRecord.record_date >= date_from)
    if date_to:
        query = query.filter(WeightRecord.record_date <= date_to)
    query = query.order_by(WeightRecord.record_date.asc(), WeightRecord.updated_at.asc())
    if limit:
        records = query.all()[-limit:]
        return records
    return query.all()


def get_weight_summary(db: Session, user_id: int, days: int = 14) -> WeightSummaryRsp:
    date_to = date.today()
    date_from = date_to - timedelta(days=max(days - 1, 0))
    records = get_weight_records(db, user_id, date_from=date_from, date_to=date_to)
    if not records:
        return WeightSummaryRsp()

    latest = records[-1]
    first = records[0]
    last_7_start = date_to - timedelta(days=6)
    records_7d = [item for item in records if item.record_date >= last_7_start]
    change_7d = 0.0
    if len(records_7d) >= 2:
        change_7d = round(records_7d[-1].weight - records_7d[0].weight, 1)

    return WeightSummaryRsp(
        latest_weight=round(latest.weight, 1),
        latest_date=latest.record_date.isoformat(),
        first_weight=round(first.weight, 1),
        change_total=round(latest.weight - first.weight, 1),
        change_7d=change_7d,
        records_count=len(records),
    )
