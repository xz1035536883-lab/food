"""Food schemas."""
from pydantic import BaseModel


class FoodNutrition(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class RecognizedFood(BaseModel):
    name: str
    confidence: float
    nutrition: FoodNutrition
    weight: int
    calories: float


class RecognizeRsp(BaseModel):
    foods: list[RecognizedFood]


class FoodSearchItem(BaseModel):
    id: int
    name: str
    category: str
    calories: float
    protein: float
    fat: float
    carbs: float


class FoodSearchRsp(BaseModel):
    foods: list[FoodSearchItem]


class FoodDetail(FoodSearchItem):
    fiber: float
    image_url: str
