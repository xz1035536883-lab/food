"""Food recognition and search router."""
import base64
import io

from fastapi import APIRouter, Depends, File, UploadFile, Query
from PIL import Image
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.food import Food
from ..services.recognition_service import recognize_food
from ..utils.response import success, fail

router = APIRouter(prefix="/api/food", tags=["食物识别"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _compress_for_api(data: bytes, max_kb: int = 3500) -> bytes:
    """Compress image to stay under API size limits."""
    if len(data) <= max_kb * 1024:
        return data
    try:
        img = Image.open(io.BytesIO(data))
        quality = 80
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=quality)
        data = buf.getvalue()
        while len(data) > max_kb * 1024 and quality > 10:
            quality -= 10
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=quality)
            data = buf.getvalue()
        if len(data) > max_kb * 1024:
            img = img.resize((img.width // 2, img.height // 2))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=75)
            data = buf.getvalue()
        return data
    except Exception:
        return data


@router.post("/recognize")
async def recognize(image: UploadFile = File(...), db: Session = Depends(get_db)):
    """Recognize food from uploaded image."""
    try:
        contents = await image.read()
        # Compress large images to stay under Baidu API 4MB limit
        contents = _compress_for_api(contents)
        image_base64 = base64.b64encode(contents).decode("utf-8")
        result = recognize_food(db, image_base64)
        return success(result.model_dump())
    except Exception as e:
        return fail(message=f"识别失败: {str(e)}")


@router.get("/search")
def search_foods(keyword: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search foods by keyword."""
    foods = (
        db.query(Food)
        .filter(Food.name.like(f"%{keyword}%"))
        .limit(20)
        .all()
    )
    result = [
        {
            "id": f.id,
            "name": f.name,
            "category": f.category,
            "calories": float(f.calories),
            "protein": float(f.protein),
            "fat": float(f.fat),
            "carbs": float(f.carbs),
        }
        for f in foods
    ]
    return success({"foods": result})


@router.get("/{food_id}")
def get_food_detail(food_id: int, db: Session = Depends(get_db)):
    """Get food detail by ID."""
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        return fail(message="食物不存在")
    return success(food.to_dict())
