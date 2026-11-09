class ReceptionError(Exception):
    """Lỗi nghiệp vụ của màn hình Tiếp đón; trả về dạng {"detail": {"code", "message"}}."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
