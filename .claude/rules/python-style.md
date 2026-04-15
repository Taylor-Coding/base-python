# Python Style Rules

## 기본 원칙

- Python 3.12+ 문법을 사용한다 (`X | Y` union 타입, `match` 문 등)
- 타입 힌트를 모든 함수 시그니처에 명시한다
- `Optional[X]` 대신 `X | None`을 사용한다
- `List[X]`, `Dict[K, V]` 대신 `list[X]`, `dict[K, V]`를 사용한다

## 금지 패턴

- `router.py` 안에 비즈니스 로직 작성 금지
- `repository.py` 안에 `HTTPException` 발생 금지 (service 레이어 책임)
- 전역 `try/except Exception` 남발 금지 — 구체적인 예외 처리

## SQLAlchemy

- ORM 쿼리는 `session.query()` 대신 `select()` 구문(2.0 스타일) 권장
- `relationship` lazy loading 주의 — 필요 시 `joinedload` 명시
- 모든 모델은 `BaseModel`을 상속한다

## Pydantic

- 응답 스키마에는 `model_config = {"from_attributes": True}` 필수
- `exclude_none=True`로 `model_dump()` 호출하여 None 필드 제외
