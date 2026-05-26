.PHONY: help dev shell test test-domain test-v lint format quality \
        migrate-new migrate-up migrate-down migrate-history \
        worker install \
        docker-build docker-run docker

IMAGE_NAME ?= dwork-studio-api
IMAGE_TAG  ?= latest

# 기본 타겟: make 만 입력하면 도움말 출력
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── 개발 서버 ─────────────────────────────────────────────
dev: ## 개발 서버 실행 (hot-reload)
	uvicorn app.main:app --reload

# ── 테스트 ───────────────────────────────────────────────
test: ## 전체 테스트 실행
	pytest

test-v: ## 전체 테스트 (상세 출력)
	pytest -v

test-domain: ## 특정 도메인 테스트  ex) make test-domain d=user
	pytest tests/domains/$(d)/

# ── 코드 품질 ─────────────────────────────────────────────
format: ## black 포맷 적용
	black app/ tests/

lint: ## black 포맷 검사 (수정 없음)
	black --check app/ tests/
	ruff check app/ tests/

quality: lint test ## lint와 test를 함께 실행

# ── Alembic 마이그레이션 ──────────────────────────────────
migrate-new: ## 마이그레이션 파일 생성  ex) make migrate-new m="add user table"
	alembic revision --autogenerate -m "$(m)"

migrate-up: ## 최신 마이그레이션 적용
	alembic upgrade head

migrate-down: ## 마이그레이션 1단계 롤백
	alembic downgrade -1

migrate-history: ## 마이그레이션 이력 출력
	alembic history --verbose

# ── Celery ───────────────────────────────────────────────
worker: ## Celery 워커 실행
	celery -A app.core.worker.celery_app worker --loglevel=info

# ── 패키지 ───────────────────────────────────────────────
install: ## 의존성 설치
	pip install -r requirements.txt

# ── Docker ───────────────────────────────────────────────
docker-build: ## Docker 이미지 빌드  ex) make docker-build IMAGE_TAG=1.0.0
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-run: ## Docker 컨테이너 실행 (Swagger 비활성화)
	docker run --rm \
		--env-file .env \
		-e DEBUG=false \
		-p 8000:8000 \
		$(IMAGE_NAME):$(IMAGE_TAG)

docker: docker-build docker-run ## 빌드 후 바로 실행
