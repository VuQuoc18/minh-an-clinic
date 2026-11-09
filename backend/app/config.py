from functools import lru_cache

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


class CorsSettings(BaseSettings):
    """Cấu hình CORS, tách riêng để tạo app không cần DATABASE_URL."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Danh sách origin được phép, ngăn cách bằng dấu phẩy. Để trống = không bật CORS.
    # "*" chỉ dùng khi dev (ví dụ xem trước trong iframe sandbox có origin "null").
    cors_allow_origins: str = ""

    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
