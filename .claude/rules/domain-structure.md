# Domain Structure Rules

## 새 도메인 추가 체크리스트

새 도메인을 추가할 때 아래 순서를 따른다.

1. `app/domains/<name>/` 생성
2. `models.py` — `BaseModel` 상속, `__tablename__` 명시
3. `schemas.py` — Create / Update / Response 스키마 분리
4. `repository.py` — `BaseRepository` 상속, 도메인 특화 쿼리만 추가
5. `service.py` — 비즈니스 로직, `HTTPException` 발생 담당
6. `router.py` — DI 조립 + 엔드포인트만, 로직 없음
7. `app/domains/<name>/__init__.py` 생성
8. `migrations/env.py`에 `import app.domains.<name>.models` 추가
9. `app/main.py`에 `app.include_router(...)` 추가
10. `tests/domains/<name>/` 아래 테스트 3종 작성

## 레이어 간 의존 규칙

```
router → service → repository → model
```

- 역방향 의존 절대 금지
- 도메인 간 직접 import 금지 — 필요 시 공통 서비스 또는 이벤트 활용

## 파일명 규칙

- 스네이크 케이스: `user_profile.py`
- 도메인 폴더명은 단수형: `user/`, `order/`, `product/`
