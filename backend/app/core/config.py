from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình đọc từ biến môi trường hoặc file .env (NFR-16: không hard-code secret)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bắt buộc, ví dụ: postgresql+psycopg://<user>:<password>@<host>:5432/<db>
    database_url: str
    timezone: str = "Asia/Ho_Chi_Minh"
    log_level: str = "INFO"
    # CHỈ DÙNG KHI DEV: nếu đặt, token này đăng nhập như Lễ tân (tạm thời đến khi có FR-TK-04).
    # Để trống ở mọi môi trường khác: khi đó mọi token đều bị từ chối.
    dev_staff_token: str | None = None
    # Danh sách origin được phép gọi API từ trình duyệt, ngăn cách bằng dấu phẩy.
    # Để trống = không bật CORS (frontend và API cùng origin qua proxy `/api`).
    # "*" chỉ dùng khi dev (ví dụ xem trước trong iframe sandbox có origin "null").
    cors_allow_origins: str = ""

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        # SpecForge sandbox và nhiều dịch vụ cấp URL dạng postgresql:// hoặc postgres://; SQLAlchemy
        # sẽ hiểu là driver psycopg2 (không cài). Đổi sang psycopg 3 đã có trong dependencies.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
