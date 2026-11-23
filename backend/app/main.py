from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import API_PREFIX, api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.security import install_dev_token_verifier


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    install_dev_token_verifier(settings.dev_staff_token)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Minh An Clinic API",
        lifespan=lifespan,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    if settings.cors_origins:
        # Xác thực bằng header Authorization (không cookie) nên không bật allow_credentials.
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    register_error_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()
