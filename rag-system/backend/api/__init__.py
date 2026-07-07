"""Shared helpers for API routers."""
from database import ROLE_LEVELS


def role_to_level(role: str) -> int:
    return ROLE_LEVELS.get(role, 1)
