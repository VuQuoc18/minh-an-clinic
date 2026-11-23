"""Gom router của các phân hệ dưới tiền tố ``/api``.

Frontend gọi ``/api/...`` cùng origin: Vite (dev), nginx (Docker) và SpecForge sandbox đều chuyển
nguyên đường dẫn ``/api`` sang backend, không cắt bớt tiền tố.
"""

from fastapi import APIRouter

from app.modules.reception.router import router as reception_router

API_PREFIX = "/api"

api_router = APIRouter(prefix=API_PREFIX)


@api_router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(reception_router)
