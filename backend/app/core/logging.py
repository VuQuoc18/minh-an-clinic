import logging


def configure_logging(level: str) -> None:
    """Ghi log ra stderr theo mức cấu hình (LOG_LEVEL); gọi một lần khi ứng dụng khởi động."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        force=True,
    )
