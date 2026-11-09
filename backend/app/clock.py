from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def get_now() -> datetime:
    """FastAPI dependency: thời điểm hiện tại theo múi giờ cấu hình (mặc định Asia/Ho_Chi_Minh)."""
    return datetime.now(ZoneInfo(get_settings().timezone))
