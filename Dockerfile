# ── Stage 1: 의존성 빌드 ──────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 컴파일에 필요한 빌드 도구 (최종 이미지에는 포함되지 않음)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성만 먼저 복사하여 레이어 캐시 최대화
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: 런타임 ──────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# psycopg2 런타임 의존성만 설치 (gcc 등 빌드 도구 제외)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# builder 스테이지에서 설치된 패키지만 복사
COPY --from=builder /install /usr/local

# 소스코드 복사 (.dockerignore로 불필요한 파일 제외)
COPY app/ ./app/
COPY alembic.ini .
COPY migrations/ ./migrations/

# 비root 유저로 실행 (보안)
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
