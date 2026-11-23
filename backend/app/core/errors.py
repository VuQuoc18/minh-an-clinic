"""Lỗi nghiệp vụ và dạng phản hồi lỗi thống nhất của API.

Mọi lỗi trả về dạng ``{"detail": {"code": "...", "message": "..."}}`` để frontend luôn có mã lỗi
và câu thông báo tiếng Việt hiển thị được. Lỗi kiểm tra dữ liệu (422) có thêm ``errors``: danh
sách ``{"field", "message"}`` cho từng trường sai.
"""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Lỗi nghiệp vụ có mã HTTP, mã lỗi máy đọc được và câu thông báo cho người dùng."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


VALIDATION_MESSAGE = "Dữ liệu gửi lên không hợp lệ."


def _field_name(loc: tuple) -> str:
    # Bỏ phần "body"/"query"/"path" ở đầu; giữ đường dẫn trường, ví dụ "new_profile.phone".
    parts = [str(p) for p in loc[1:]] if len(loc) > 1 else [str(p) for p in loc]
    return ".".join(parts)


def _clean_message(message: str) -> str:
    # Pydantic thêm tiền tố "Value error, " cho ValueError do validator của mình ném ra.
    return message.removeprefix("Value error, ")


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": _field_name(tuple(err.get("loc", ()))), "message": _clean_message(err["msg"])}
        for err in exc.errors()
    ]
    # Validator tự viết có câu tiếng Việt: dùng làm thông báo chính nếu chỉ có một lỗi.
    message = errors[0]["message"] if len(errors) == 1 else VALIDATION_MESSAGE
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": {"code": "VALIDATION_ERROR", "message": message, "errors": errors}}
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
