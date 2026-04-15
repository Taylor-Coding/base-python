# Commit Message Rules

## Format

```
type(scope): Subject
```

- `type`은 소문자로 작성한다
- `(scope)`는 영향 범위를 나타내며 선택 사항이다
- Subject 첫 글자는 대문자로 시작하고 동사 원형(명령형)을 사용한다
- 요약줄은 50자 이내, 끝에 마침표를 찍지 않는다

## Types

| Type | 용도 |
| --- | --- |
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `perf` | 성능 개선 |
| `refactor` | 기능 변경 없이 코드 구조 개선 |
| `docs` | 문서 수정 |
| `test` | 테스트 추가 또는 수정 |
| `chore` | 빌드 설정, 패키지 업데이트 등 |
| `style` | 포맷, 세미콜론 등 코드 의미 변경 없는 수정 |

## Good Examples

```
feat(auth): Add password encryption for login
perf(main): Implement lazy loading for images
fix(api): Update incorrect user profile endpoint
docs: Update README with installation instructions
test(user): Add service layer unit tests
refactor(repository): Extract common query into BaseRepository
```

## Bad Examples

```
Added login feature      # type 없음, 과거형
fix: fixed bug           # 과거형 사용 (fixed → fix)
Refactoring code         # 현재진행형 사용
update                   # 무엇을 수정했는지 불명확
```
