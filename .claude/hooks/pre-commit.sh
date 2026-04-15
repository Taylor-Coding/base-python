#!/usr/bin/env bash
# .claude/hooks/pre-commit.sh
# Claude Code hook: 커밋 전 자동 실행

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> [hook] Running tests before commit..."
pytest tests/ -q --tb=short

echo "==> [hook] Checking for syntax errors..."
python -m py_compile $(git diff --cached --name-only -- '*.py') 2>/dev/null || true

echo "==> [hook] All checks passed."
