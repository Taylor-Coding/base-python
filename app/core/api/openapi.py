from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

tags_metadata = [
    {"name": "auth", "description": "회원가입 및 로그인"},
    {"name": "users", "description": "사용자 조회 및 관리"},
]

# 인증이 필요 없는 태그
_PUBLIC_TAGS = {"auth"}


def configure_openapi(app: FastAPI) -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description="flody API",
            routes=app.routes,
            tags=tags_metadata,
        )

        schema.setdefault("components", {})
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }

        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                if isinstance(operation, dict):
                    if not set(operation.get("tags", [])).intersection(_PUBLIC_TAGS):
                        operation["security"] = [{"BearerAuth": []}]

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
