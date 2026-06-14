"""Authentication service - WeChat login + JWT."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import jwt
import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User
from ..schemas.auth import LoginRsp, UserInfo


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
    else:
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        db.flush()
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
