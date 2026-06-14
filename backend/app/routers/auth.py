"""Auth router."""
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.user import User
from ..services import auth_service, plan_service
from ..schemas.auth import LoginReq, UserUpdateReq
from ..utils.response import success, fail

router = APIRouter(prefix="/api/auth", tags=["认证"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(authorization: str = Header(None)) -> int:
    """Dependency: extract user_id from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return 0
    token = authorization[7:]
    db = SessionLocal()
    try:
        user = auth_service.get_current_user(db, token)
        return user.id if user else 0
    finally:
        db.close()


def _build_profile_payload(user: User) -> dict:
    payload = user.to_dict()
    payload["profile_summary"] = plan_service.build_profile_summary(payload)
    return payload


def _validate_profile_update(req: UserUpdateReq, current_user: User) -> Optional[str]:
    if req.gender is not None and req.gender not in {"male", "female", ""}:
        return "性别仅支持 male 或 female"
    if req.age is not None and not 1 <= req.age <= 120:
        return "年龄需在 1-120 岁之间"
    if req.height is not None and not 80 <= req.height <= 260:
        return "身高需在 80-260 cm 之间"
    if req.weight is not None and not 20 <= req.weight <= 500:
        return "体重需在 20-500 kg 之间"
    if req.target_weight is not None and not 20 <= req.target_weight <= 500:
        return "目标体重需在 20-500 kg 之间"
    if req.daily_calorie_target is not None and not 800 <= req.daily_calorie_target <= 5000:
        return "每日热量目标需在 800-5000 kcal 之间"

    weight = req.weight if req.weight is not None else current_user.weight
    target_weight = req.target_weight if req.target_weight is not None else current_user.target_weight
    if weight and target_weight and target_weight >= weight * 1.5:
        return "目标体重异常，请检查输入"

    return None


@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    """WeChat mini-program login."""
    try:
        result = auth_service.login(db, req.code)
        return success(result.model_dump())
    except Exception as e:
        return fail(message=str(e))


@router.get("/profile")
def get_profile(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """Get current user profile."""
    if not user_id:
        return fail(code=401, message="未登录")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return fail(message="用户不存在")
    return success(_build_profile_payload(user))


@router.post("/profile")
def update_profile(
    req: UserUpdateReq,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Update user profile."""
    if not user_id:
        return fail(code=401, message="未登录")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return fail(message="用户不存在")
    error_message = _validate_profile_update(req, user)
    if error_message:
        return fail(message=error_message)

    update_fields = [
        ("nickname", req.nickname),
        ("avatar_url", req.avatar_url),
        ("daily_calorie_target", req.daily_calorie_target),
        ("gender", req.gender),
        ("age", req.age),
        ("height", req.height),
        ("weight", req.weight),
        ("target_weight", req.target_weight),
    ]
    for field_name, value in update_fields:
        if value is not None:
            setattr(user, field_name, value)

    db.commit()
    db.refresh(user)
    return success(_build_profile_payload(user))


@router.get("/plan")
def get_plan(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """Generate weight loss plan based on user body profile."""
    if not user_id:
        return fail(code=401, message="未登录")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return fail(message="用户不存在")

    # Validate required fields
    if not user.gender or not user.age or not user.height or not user.weight:
        return fail(message="请先完善个人信息（性别、年龄、身高、体重）")

    if not user.target_weight:
        return fail(message="请设置目标体重")

    try:
        user_payload = user.to_dict()
        plan_data = plan_service.generate_plan(user_payload)
        if user.daily_calorie_target != plan_data["daily_calorie_target"]:
            user.daily_calorie_target = plan_data["daily_calorie_target"]
            db.commit()
            db.refresh(user)
            user_payload = user.to_dict()
        return success({
            "plan": plan_data,
            "profile_summary": plan_service.build_profile_summary(user_payload),
        })
    except Exception as e:
        return fail(message=str(e))
