from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import install_dev_token_verifier
from app.config import CorsSettings, get_settings
from app.reception.errors import ReceptionError
from app.reception.router import router as reception_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    install_dev_token_verifier(get_settings().dev_staff_token)
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Minh An Clinic API", lifespan=lifespan)
    origins = CorsSettings().origins()
    if origins:
        # Xác thực bằng header Authorization (không cookie) nên không bật allow_credentials.
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    application.include_router(reception_router)
    application.add_exception_handler(ReceptionError, reception_error_handler)
    application.add_api_route("/health", health, methods=["GET"])
    return application


def reception_error_handler(_request: Request, exc: ReceptionError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


def health() -> dict[str, str]:
    return {"status": "ok"}


app = create_app()
