"""Minimal message catalog for English (primary) and Vietnamese (spec §2).

Keep API-facing messages here so both languages stay in sync. The client
(Flutter) has its own ARB-based localization for UI labels; this catalog is
only for server-generated messages (errors, scheduler diagnostics, ...).
"""

from __future__ import annotations

from app.core.config import settings

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "auth.invalid_credentials": "Incorrect username or password.",
        "auth.inactive_user": "User account is not active.",
        "auth.admin_required": "Admin privileges are required.",
        "schedule.infeasible": "No valid schedule could be found.",
    },
    "vi": {
        "auth.invalid_credentials": "Sai tên đăng nhập hoặc mật khẩu.",
        "auth.inactive_user": "Tài khoản chưa được kích hoạt.",
        "auth.admin_required": "Yêu cầu quyền quản trị.",
        "schedule.infeasible": "Không tìm được lời giải hợp lệ cho lịch.",
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key; falls back to the key itself if missing."""
    language = lang or settings.DEFAULT_LANGUAGE
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)
