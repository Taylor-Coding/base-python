# Project Guide

## Overview

FastAPI + SQLAlchemy 기반의 REST API 서버.

- **언어**: Python 3.12
- **프레임워크**: FastAPI, SQLAlchemy 2.0
- **DB**: PostgreSQL (테스트: SQLite 인메모리)
- **인증**: JWT Bearer (access + refresh token)
- **비동기 작업**: Celery + Redis

## Architecture

도메인 중심 레이어 구조. 각 도메인은 독립적인 5개 파일로 구성된다.

```
domains/<name>/
  models.py      # SQLAlchemy ORM 모델
  schemas.py     # Pydantic 입출력 스키마
  repository.py  # DB 쿼리 (BaseRepository 상속)
  service.py     # 비즈니스 로직, HTTPException 발생 지점
  router.py      # FastAPI 엔드포인트
```

**의존 방향**: router → service → repository → model (단방향)

## Commands

```bash
# 개발 서버 실행
uvicorn app.main:app --reload

# 테스트 실행
pytest

# 특정 도메인 테스트
pytest tests/domains/user/

# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# Celery 워커 실행
celery -A app.integrations.celery_app worker --loglevel=info
```

## Coding Rules

- 모든 비즈니스 로직은 `service.py`에, DB 쿼리는 `repository.py`에만 작성한다
- `router.py`는 DI 조립과 HTTP 변환만 담당한다 (로직 금지)
- 새 도메인 추가 시 `migrations/env.py`에 모델 import를 추가해야 Alembic이 감지한다
- 테스트는 라우터(엔드포인트) 단위로만 작성한다 — service/repository 단위 테스트는 작성하지 않는다
- 테스트는 SQLite 인메모리 DB를 사용하며 트랜잭션 롤백으로 격리한다
- `BaseModel`, `BaseRepository`를 반드시 상속한다 (`id`, `created_at`, `updated_at` 자동 포함)

## Adding a New Domain

1. `app/domains/<name>/` 디렉터리 생성 후 5개 파일 작성
2. `migrations/env.py`에 `import app.domains.<name>.models` 추가
3. `app/main.py`에 라우터 등록: `app.include_router(router, prefix="/api/v1")`
4. `tests/domains/<name>/test_router.py` 작성 (라우터 테스트만)

## Commit Message

`type(scope): Subject` 형식을 따른다. 자세한 규칙은 [.claude/rules/commit-message.md](.claude/rules/commit-message.md) 참고.

```
feat(auth): Add password encryption for login
fix(api): Update incorrect user profile endpoint
test(user): Add router integration tests
```

- `type`은 소문자, Subject는 동사 원형(명령형), 50자 이내, 마침표 없음
- 과거형(`fixed`), 현재진행형(`Refactoring`) 사용 금지

## Environment Variables

`.env.example` 참고. 실제 값은 `.env`에 작성 (git 제외).

핵심 변수:
- `DATABASE_URL` — PostgreSQL 연결 문자열
- `JWT_SECRET_KEY` — JWT 서명 키 (운영 환경에서 반드시 변경)
- `REDIS_URL` — Redis 연결 (캐시 + Celery 브로커)
