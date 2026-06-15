"""Authentication service - WeChat login + JWT."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

import jwt
import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User
from ..schemas.auth import LoginRsp, UserInfo

# Random nickname generator
_ADJECTIVES = [
    "快乐的", "阳光的", "活力", "元气", "轻盈", "健康的",
    "勤奋的", "闪亮的", "可爱的", "自律的", "勇敢的", "幸运的",
]
_NOUNS = [
    "小布丁", "小太阳", "小星星", "向日葵", "蓝胖子",
    "小精灵", "糯米团", "棉花糖", "小青柠", "泡芙",
    "麦旋风", "小丸子", "跳跳糖", "甜甜圈", "舒芙蕾",
]


def _generate_nickname(user_id: int) -> str:
    """Generate a random but stable nickname for a new user."""
    random.seed(user_id * 31 + 7)
    adj = random.choice(_ADJECTIVES)
    noun = random.choice(_NOUNS)
    return f"{adj}{noun}"


def _get_wechat_openid(code: str) -> dict:
    """Call WeChat API to exchange code for openid and session_key."""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if "errcode" in data and data["errcode"] != 0:
        raise Exception(f"WeChat login failed: {data.get('errmsg', 'unknown')}")
    return data


def _generate_token(user_id: int) -> str:
    """Generate JWT token."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> int:
    """Decode JWT token and return user_id. Raises on invalid/expired."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return payload["user_id"]


def login(db: Session, code: str, nickname: str = "", avatar_url: str = "") -> LoginRsp:
    """WeChat mini-program login. Creates user if new."""
    wx_data = _get_wechat_openid(code)
    openid = wx_data["openid"]

    user = db.query(User).filter(User.openid == openid).first()

    if user is None:
        user = User(
            openid=openid,
            nickname=nickname,
            avatar_url=avatar_url,
        )
        db.add(user)
        db.flush()
        # Assign random nickname for new users
        if not nickname:
            user.nickname = _generate_nickname(user.id)
    else:
        if nickname:
            user.nickname = nickname
        elif not user.nickname:
            # Assign random nickname to existing users who don't have one yet
            user.nickname = _generate_nickname(user.id)
    if avatar_url and user.avatar_url != avatar_url:
        user.avatar_url = avatar_url

    db.commit()

    token = _generate_token(user.id)

    return LoginRsp(
        token=token,
        user=UserInfo(
            id=user.id,
            nickname=user.nickname or "",
            avatar_url=user.avatar_url or "",
            daily_calorie_target=user.daily_calorie_target,
            gender=user.gender or "",
            age=user.age,
            height=user.height,
            weight=user.weight,
            target_weight=user.target_weight,
        ),
    )


def get_current_user(db: Session, token: str) -> User | None:
    """Get user from token. Returns None if invalid."""
    try:
        user_id = decode_token(token)
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None
