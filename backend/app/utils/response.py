"""Unified response format."""
from typing import Any, Optional


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int = 1, message: str = "error", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
