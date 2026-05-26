from typing import cast

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.types import ASGIApp

from app.core.api.dependencies import get_current_user
from app.core.api.exceptions import register_exception_handlers
from app.core.api.logging import request_logging_middleware
from app.core.api.openapi import configure_openapi, tags_metadata
from app.core.clients.redis import redis_ping
from app.core.config.settings import settings
from app.core.database.session import engine
from app.domains.auth.routers.auth_router import router as auth_router
from app.domains.user.routers.user_router import router as user_router

api_prefix = settings.api_prefix

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url=f"{api_prefix}/docs" if settings.DEBUG else None,
    redoc_url=f"{api_prefix}/redoc" if settings.DEBUG else None,
    openapi_url=f"{api_prefix}/openapi.json",
    openapi_tags=tags_metadata,
)

configure_openapi(app)


def create_cors_middleware(app: ASGIApp) -> ASGIApp:
    return cast(
        ASGIApp,
        CORSMiddleware(
            app,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    )


app.add_middleware(create_cors_middleware)

register_exception_handlers(app)
app.middleware("http")(request_logging_middleware)

# Public: 인증 불필요 (auth 흐름 전체)
app.include_router(auth_router, prefix=api_prefix)

# Protected: 모든 엔드포인트에 get_current_user 적용
app.include_router(user_router, prefix=api_prefix, dependencies=[Depends(get_current_user)])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def readiness_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    redis_ping()
    return {"status": "ready", "env": settings.APP_ENV}
