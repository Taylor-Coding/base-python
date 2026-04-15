# DWork AI Studio API

FastAPI 기반의 DWork AI Studio 백엔드 API 서버입니다.

## 기술 스택

- **Runtime**: Python 3.12
- **Framework**: FastAPI 0.115
- **Language**: Python
- **Database**: PostgreSQL (SQLAlchemy 2.0)
- **Package Manager**: pip

## 사전 요구사항

- Python 3.12 이상
- PostgreSQL
- Redis

## 프로젝트 셋업

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

또는 Makefile 사용:

```bash
make install
```

### 2. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```


### 3. 데이터베이스 마이그레이션 실행

```bash
make migrate-up
```

### 4. 개발 서버 실행

```bash
make dev
```

서버가 `http://localhost:8000`에서 실행됩니다.  
`DEBUG=true` 환경에서는 Swagger UI(`/docs`)와 ReDoc(`/redoc`)이 활성화됩니다.

---

## 스크립트

### 서버 실행

| 명령어 | 설명 |
| ------ | ---- |
| `make dev` | 개발 서버 실행 (hot-reload) |

### 테스트

| 명령어 | 설명 |
| ------ | ---- |
| `make test` | 전체 테스트 실행 |
| `make test-v` | 전체 테스트 (상세 출력) |
| `make test-domain d=<name>` | 특정 도메인 테스트 (예: `make test-domain d=user`) |

### 코드 품질

| 명령어 | 설명 |
| ------ | ---- |
| `make format` | black 포맷 적용 |
| `make lint` | black 포맷 검사 (수정 없음) |

### 데이터베이스 마이그레이션

| 명령어 | 설명 |
| ------ | ---- |
| `make migrate-new m="<description>"` | 마이그레이션 파일 생성 |
| `make migrate-up` | 최신 마이그레이션 적용 |
| `make migrate-down` | 마지막 마이그레이션 롤백 |
| `make migrate-history` | 마이그레이션 이력 출력 |

### Celery 워커

| 명령어 | 설명 |
| ------ | ---- |
| `make worker` | Celery 워커 실행 |

### Docker

| 명령어 | 설명 |
| ------ | ---- |
| `make docker-build` | Docker 이미지 빌드 |
| `make docker-run` | Docker 컨테이너 실행 |
| `make docker` | 빌드 후 바로 실행 |
