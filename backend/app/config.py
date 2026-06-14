"""Application configuration."""
import os


class Settings:
    APP_NAME: str = "Food Calorie Recognition API"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./food_calorie.db",
    )

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 720  # 30 days

    # WeChat Mini Program
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")

    # Baidu AI - Dish Recognition
    BAIDU_API_KEY: str = os.getenv("BAIDU_API_KEY", "")
    BAIDU_SECRET_KEY: str = os.getenv("BAIDU_SECRET_KEY", "")

    # Upload
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Default portion weight estimates (grams)
    DEFAULT_PORTIONS: dict = {
        "主食": 200,
        "肉类": 150,
        "蔬菜": 200,
        "水果": 200,
        "饮品": 300,
        "零食": 100,
        "汤品": 300,
        "其他": 150,
    }


settings = Settings()
