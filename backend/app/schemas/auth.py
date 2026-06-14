"""Auth schemas."""
from typing import Optional
from pydantic import BaseModel


class LoginReq(BaseModel):
    code: str


class UserInfo(BaseModel):
    id: int
    nickname: str
    avatar_url: str
    daily_calorie_target: int
    gender: str = ""
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None


class LoginRsp(BaseModel):
    token: str
    user: UserInfo


class UserUpdateReq(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    daily_calorie_target: Optional[int] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None


class ProfileSummary(BaseModel):
    completion: int
    missing_fields: list[str]
    is_complete: bool


class MilestoneInfo(BaseModel):
    stage: str
    weeks: str
    focus: str


class AdviceInfo(BaseModel):
    diet: list[str]
    exercise: list[str]
    lifestyle: list[str]


class ProtocolInfo(BaseModel):
    daily_deficit: int
    weekly_weight_change: float
    weigh_in_frequency: str
    review_cycle: str
    warning: str


class MealBudgetInfo(BaseModel):
    breakfast: int
    lunch: int
    dinner: int
    snack: int


class PlanInfo(BaseModel):
    bmi: float
    bmi_category: str
    target_bmi: float
    bmr: float
    tdee: float
    activity_factor: float
    daily_calorie_target: int
    daily_deficit: int
    weight_to_lose: float
    estimated_weeks: int
    breakfast_cal: int
    lunch_cal: int
    dinner_cal: int
    snack_cal: int
    meal_budget: MealBudgetInfo
    profile_summary: ProfileSummary
    milestones: list[MilestoneInfo]
    advice: AdviceInfo
    protocol: ProtocolInfo
    tips: list[str]


class PlanRsp(BaseModel):
    plan: PlanInfo


class UserProfileRsp(UserInfo):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    profile_summary: ProfileSummary
