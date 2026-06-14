"""FastAPI application entry point."""
import os
import sys

# Ensure the backend directory is in sys.path for seed data imports
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Load .env before importing settings
from dotenv import load_dotenv
load_dotenv(os.path.join(_backend_dir, ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, SessionLocal
from .models.food import Food
from .models.weight_record import WeightRecord
from .routers import auth, food, diet_record, weight_record

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None,
)

# CORS middleware - allow mini-program requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(food.router)
app.include_router(diet_record.router)
app.include_router(weight_record.router)


@app.on_event("startup")
def on_startup():
    """Initialize database and seed data on startup."""
    init_db()
    _migrate_user_table()
    _seed_foods_if_empty()
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _migrate_user_table():
    """Add new columns to user table if they don't exist (SQLite migration)."""
    from sqlalchemy import inspect, text
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        columns = {c["name"] for c in inspector.get_columns("user")}
        new_columns = {
            "gender": "VARCHAR(8) DEFAULT ''",
            "age": "INTEGER",
            "height": "FLOAT",
            "weight": "FLOAT",
            "target_weight": "FLOAT",
        }
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                db.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"))
                print(f"[Migrate] Added column user.{col_name}")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Migrate] Migration skipped: {e}")
    finally:
        db.close()


def _seed_foods_if_empty():
    """Insert seed food data if food table is empty."""
    db = SessionLocal()
    try:
        count = db.query(Food).count()
        if count > 0:
            return

        from data.seed_foods import FOODS
        foods = [
            Food(
                name=name,
                category=category,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs,
                fiber=fiber,
            )
            for name, category, calories, protein, fat, carbs, fiber in FOODS
        ]
        db.add_all(foods)
        db.commit()
        print(f"[Seed] Inserted {len(foods)} food items.")
    finally:
        db.close()


# Health check
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}
