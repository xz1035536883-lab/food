"""Food recognition service using Baidu AI Dish Recognition API.

Baidu API returns dish name, calorie (per 100g), and confidence.
Local database is used to supplement protein/fat/carbs/fiber data.
"""
from __future__ import annotations

import time
from typing import Optional

import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.food import Food
from ..schemas.food import RecognizeRsp, RecognizedFood, FoodNutrition

# Module-level access_token cache (valid for 30 days)
_token_cache: Optional[str] = None
_token_expires_at: float = 0

# Rate limiter: Baidu free tier QPS = 1, enforce 1.5s between calls
_last_api_call: float = 0
_MIN_INTERVAL = 1.5  # seconds


def _get_access_token() -> str:
    """Get a cached Baidu OAuth access_token, refreshing if needed."""
    global _token_cache, _token_expires_at

    if _token_cache and time.time() < _token_expires_at - 3600:
        return _token_cache

    resp = requests.get(
        "https://aip.baidubce.com/oauth/2.0/token",
        params={
            "grant_type": "client_credentials",
            "client_id": settings.BAIDU_API_KEY,
            "client_secret": settings.BAIDU_SECRET_KEY,
        },
        timeout=10,
    )
    data = resp.json()
    if "access_token" not in data:
        raise Exception(f"Baidu OAuth error: {data.get('error_description', str(data))}")

    _token_cache = data["access_token"]
    _token_expires_at = time.time() + data.get("expires_in", 2592000)
    return _token_cache


def _call_baidu_dish_api(image_base64: str, top_num: int = 5) -> list[dict]:
    """Call Baidu AI Dish Recognition v2 API with QPS rate limiting."""
    global _last_api_call

    token = _get_access_token()

    # Rate limit: wait until at least MIN_INTERVAL since last call
    elapsed = time.time() - _last_api_call
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    # Encode image for urlencoded form body
    image_encoded = requests.utils.quote(image_base64)

    max_retries = 3
    for attempt in range(max_retries):
        _last_api_call = time.time()
        resp = requests.post(
            "https://aip.baidubce.com/rest/2.0/image-classify/v2/dish",
            params={"access_token": token},
            data=f"image={image_encoded}&top_num={top_num}&filter_threshold=0.5",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        data = resp.json()

        if "error_code" not in data:
            return data.get("result", [])

        error_code = data["error_code"]
        # QPS limit (18/19) — retry after longer delay
        if error_code in (18, 19) and attempt < max_retries - 1:
            time.sleep(2.0)
            continue

        raise Exception(f"Baidu API error [{error_code}]: {data.get('error_msg', str(data))}")

    return []


def _match_food_in_db(db: Session, name: str) -> Optional[Food]:
    """Fuzzy match recognized food name to local nutrition database."""
    # Exact match first
    food = db.query(Food).filter(Food.name == name).first()
    if food:
        return food

    # Contains match
    food = db.query(Food).filter(Food.name.like(f"%{name}%")).first()
    if food:
        return food

    # Partial keyword match (try longer substrings of the name)
    for i in range(len(name) - 1):
        keyword = name[i:i+2]
        food = db.query(Food).filter(Food.name.like(f"%{keyword}%")).first()
        if food:
            return food

    return None


def _estimate_weight(category: str) -> int:
    """Estimate portion weight based on food category."""
    return settings.DEFAULT_PORTIONS.get(category, settings.DEFAULT_PORTIONS.get("其他", 150))


def recognize_food(db: Session, image_base64: str) -> RecognizeRsp:
    """Recognize food from image using Baidu AI, match to local nutrition DB."""
    raw_foods = _call_baidu_dish_api(image_base64)

    foods: list[RecognizedFood] = []
    for item in raw_foods:
        name = item.get("name", "未知食物")
        probability = item.get("probability", 0)
        confidence = float(probability) if isinstance(probability, str) else probability
        has_calorie = item.get("has_calorie", False)

        # Match to local database for protein/fat/carbs/fiber
        db_food = _match_food_in_db(db, name)
        weight = _estimate_weight(db_food.category if db_food else "其他")

        # Baidu API provides calorie per 100g
        baidu_calorie_per_100g = 0
        if has_calorie:
            baidu_calorie_per_100g = float(item.get("calorie", 0))

        if db_food:
            nutrition = FoodNutrition(
                calories=float(db_food.calories),
                protein=float(db_food.protein),
                fat=float(db_food.fat),
                carbs=float(db_food.carbs),
                fiber=float(db_food.fiber),
            )
            # Prefer Baidu calorie if available, fallback to DB
            if has_calorie and baidu_calorie_per_100g > 0:
                nutrition.calories = baidu_calorie_per_100g
        elif has_calorie and baidu_calorie_per_100g > 0:
            # Food not in DB but Baidu has calorie data
            nutrition = FoodNutrition(
                calories=baidu_calorie_per_100g,
                protein=0, fat=0, carbs=0, fiber=0,
            )
        else:
            # No data available at all
            nutrition = FoodNutrition(
                calories=0, protein=0, fat=0, carbs=0, fiber=0,
            )

        ratio = weight / 100.0
        calories = round(nutrition.calories * ratio, 2)

        foods.append(RecognizedFood(
            name=name,
            confidence=round(confidence, 4),
            nutrition=nutrition,
            weight=weight,
            calories=calories,
        ))

    return RecognizeRsp(foods=foods)
