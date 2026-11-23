import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.clock import get_now
from app.core.db import get_db
from app.modules.auth import service
from app.modules.auth.schemas import LoginOut, LoginRequest

Db = Annotated[Session, Depends(get_db)]
Now = Annotated[dt.datetime, Depends(get_now)]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/patient/login", response_model=LoginOut)
def patient_login(body: LoginRequest, db: Db, now: Now) -> LoginOut | JSONResponse:
    """FR-TK-01. Lỗi có dạng ``{"detail": {"code", "message", ...}}`` như các API khác."""
    try:
        return service.login(db, body.so_dien_thoai, body.mat_khau, now)
    except service.LoginRejected as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code, "message": exc.message, **exc.extra}},
        )
