---
name: auto-test
description: 변경된 파일 기반으로 대응 테스트를 자동 실행하고 결과를 보고한다
---

# Skill: auto-test

## 트리거

`/auto-test [target]` 또는 파일 저장 후 테스트 자동 실행 요청 시

## 동작

변경된 파일 또는 지정 대상에 대한 테스트를 자동으로 실행하고 결과를 보고한다.

## Steps

1. 변경된 파일 감지
   ```bash
   git diff --name-only HEAD -- '*.py'
   ```

2. 대상 도메인 추출 (예: `app/domains/user/service.py` → `tests/domains/user/`)

3. 해당 테스트 실행
   ```bash
   pytest tests/domains/<domain>/ -v --tb=short
   ```

4. 실패 시 에러 메시지와 함께 원인 분석 및 수정 제안

## 전체 테스트 실행

```bash
pytest --tb=short -q
```

## 커버리지 포함 실행

```bash
pytest --cov=app --cov-report=term-missing -q
```

## 주의사항

- 테스트 DB는 SQLite 인메모리이므로 PostgreSQL 전용 기능은 별도 확인 필요
- Celery 태스크 테스트는 `task.apply()` 동기 실행으로 처리
