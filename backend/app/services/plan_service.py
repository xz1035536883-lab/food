"""Weight loss plan generation service."""

from __future__ import annotations


PROFILE_FIELDS = [
    ("gender", "性别"),
    ("age", "年龄"),
    ("height", "身高"),
    ("weight", "当前体重"),
    ("target_weight", "目标体重"),
]


def calculate_bmi(weight: float, height: float) -> float:
    """BMI = weight(kg) / height(m)^2"""
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "偏瘦"
    elif bmi < 24:
        return "正常"
    elif bmi < 28:
        return "偏胖"
    else:
        return "肥胖"


def calculate_bmr(gender: str, weight: float, height: float, age: int) -> float:
    """Mifflin-St Jeor equation."""
    if gender == "male":
        return round(10 * weight + 6.25 * height - 5 * age + 5, 0)
    else:
        return round(10 * weight + 6.25 * height - 5 * age - 161, 0)


def get_missing_profile_fields(user: dict) -> list[str]:
    return [label for key, label in PROFILE_FIELDS if not user.get(key)]


def build_profile_summary(user: dict) -> dict:
    missing_fields = get_missing_profile_fields(user)
    completion = round(((len(PROFILE_FIELDS) - len(missing_fields)) / len(PROFILE_FIELDS)) * 100)
    return {
        "completion": completion,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
    }


def _get_activity_factor(bmi: float, age: int) -> float:
    if bmi >= 28:
        return 1.15
    if age >= 45:
        return 1.18
    return 1.2


def _get_daily_deficit(weight_to_lose: float, bmi: float) -> int:
    if weight_to_lose <= 0:
        return 0
    if bmi >= 28:
        return 600
    if bmi >= 24 or weight_to_lose >= 10:
        return 500
    return 350


def _build_milestones(estimated_weeks: int, weight_to_lose: float) -> list[dict]:
    if weight_to_lose <= 0:
        return [
            {"stage": "维持期", "weeks": "长期", "focus": "维持体重稳定，规律训练与均衡饮食"},
        ]

    total_weeks = max(estimated_weeks, 1)
    return [
        {"stage": "适应期", "weeks": f"第 1-{min(2, total_weeks)} 周", "focus": "建立记录习惯，优先稳定作息与饮水"},
        {"stage": "减脂启动", "weeks": f"第 {min(3, total_weeks)}-{min(6, total_weeks)} 周", "focus": "控制热量缺口，提升蛋白质占比"},
        {"stage": "平台突破", "weeks": f"第 {min(7, total_weeks)}-{min(10, total_weeks)} 周", "focus": "根据体重变化微调摄入与活动量"},
        {"stage": "巩固塑形", "weeks": f"第 {min(11, total_weeks)} 周后", "focus": "逐步回到维持热量，避免反弹"},
    ]


def _build_advice(weight_to_lose: float, daily_target: int, bmi: float) -> dict:
    diet = [
        "每餐优先蛋白质和高纤维蔬菜，减少精制糖与油炸食品",
        "早餐 30%、午餐 40%、晚餐 25%、加餐 5% 控制更稳定",
    ]
    exercise = [
        "每周 3-4 次力量训练，配合 2-4 次中低强度有氧",
        "每天尽量保证 7000-10000 步基础活动量",
    ]
    lifestyle = [
        "睡眠保持 7-8 小时，降低暴食和恢复不足风险",
        "每周固定 1 次晨起空腹称重，观察趋势而不是单日波动",
    ]

    if daily_target <= 1400:
        diet.append("当前目标摄入较低，建议提高食物密度质量，避免饥饿性反扑")
    if bmi >= 28:
        exercise.append("体重基数较高时，优先低冲击运动，减少膝踝负担")
    if weight_to_lose <= 0:
        diet[0] = "当前更适合体重维持与体脂优化，避免过度节食"

    return {
        "diet": diet,
        "exercise": exercise,
        "lifestyle": lifestyle,
    }


def generate_plan(user: dict) -> dict:
    """
    Generate a weight loss plan based on user's body profile.
    user dict must have: gender, age, height, weight, target_weight
    """
    gender = user.get("gender", "female")
    age = user["age"]
    height = user["height"]
    weight = user["weight"]
    target_weight = user["target_weight"]

    bmi = calculate_bmi(weight, height)
    target_bmi = calculate_bmi(target_weight, height)
    bmr = calculate_bmr(gender, weight, height, age)
    activity_factor = _get_activity_factor(bmi, age)
    tdee = round(bmr * activity_factor, 0)

    weight_to_lose = max(0, weight - target_weight)
    profile_summary = build_profile_summary(user)

    # Safe deficit: 500 kcal/day for 0.5kg/week loss
    if weight_to_lose > 0:
        daily_deficit = _get_daily_deficit(weight_to_lose, bmi)
        # Don't go below minimum calories
        min_cal = 1500 if gender == "male" else 1200
        daily_target = max(min_cal, int(tdee - daily_deficit))
        estimated_weeks = max(1, round(weight_to_lose * 7700 / (daily_deficit * 7)))
    else:
        daily_deficit = 0
        daily_target = int(tdee)
        estimated_weeks = 0

    # Meal distribution
    breakfast_cal = round(daily_target * 0.30)
    lunch_cal = round(daily_target * 0.40)
    dinner_cal = round(daily_target * 0.25)
    snack_cal = round(daily_target * 0.05)

    # Tips
    tips = []
    if weight_to_lose > 0:
        tips.append(f"目标减重 {weight_to_lose:.1f}kg，预计需 {estimated_weeks} 周")
        tips.append(f"每天制造 {daily_deficit} 千卡热量缺口，兼顾效率与可持续性")
        tips.append("早餐吃好 (30%)，午餐吃饱 (40%)，晚餐吃少 (25%)")
        if daily_target <= 1500:
            tips.append("热量摄入已接近最低安全值，建议增加运动消耗")
        tips.append("每周进行 3-5 次有氧运动，每次 30 分钟以上")
        tips.append("保证每天 2000ml 饮水量")
    else:
        tips.append("当前体重已在目标范围内，建议保持均衡饮食")
        tips.append("维持每日热量摄入与消耗平衡")
        tips.append("每周进行 2-3 次力量训练，保持肌肉量")

    milestones = _build_milestones(estimated_weeks, weight_to_lose)
    advice = _build_advice(weight_to_lose, daily_target, bmi)
    weekly_weight_change = round(daily_deficit * 7 / 7700, 2) if daily_deficit > 0 else 0
    meal_budget = {
        "breakfast": breakfast_cal,
        "lunch": lunch_cal,
        "dinner": dinner_cal,
        "snack": snack_cal,
    }
    protocol = {
        "daily_deficit": daily_deficit,
        "weekly_weight_change": weekly_weight_change,
        "weigh_in_frequency": "每周 1 次",
        "review_cycle": "每 7 天复盘一次记录与体重趋势",
        "warning": "避免极低热量、补偿性暴食和连续高强度空腹有氧",
    }

    return {
        "bmi": bmi,
        "bmi_category": bmi_category(bmi),
        "target_bmi": target_bmi,
        "bmr": bmr,
        "tdee": tdee,
        "activity_factor": activity_factor,
        "daily_calorie_target": daily_target,
        "daily_deficit": daily_deficit,
        "weight_to_lose": round(weight_to_lose, 1),
        "estimated_weeks": estimated_weeks,
        "breakfast_cal": breakfast_cal,
        "lunch_cal": lunch_cal,
        "dinner_cal": dinner_cal,
        "snack_cal": snack_cal,
        "meal_budget": meal_budget,
        "profile_summary": profile_summary,
        "milestones": milestones,
        "advice": advice,
        "protocol": protocol,
        "tips": tips,
    }
