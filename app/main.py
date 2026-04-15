from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.openapi import configure_openapi, tags_metadata
from app.dependencies import get_current_user
from app.domains.auth.router import router as auth_router
from app.domains.user.router import router as user_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_tags=tags_metadata,
)

configure_openapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Public: 인증 불필요 (auth 흐름 전체)
app.include_router(auth_router, prefix="/api")

# Protected: 모든 엔드포인트에 get_current_user 적용
app.include_router(user_router, prefix="/api", dependencies=[Depends(get_current_user)])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
