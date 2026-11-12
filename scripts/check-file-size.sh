#!/usr/bin/env bash
# Fails if any source file has more than 500 non-blank lines.
set -euo pipefail
MAX=500
fail=0
while IFS= read -r f; do
  n=$(grep -cve '^\s*$' "$f" || true)
  if [ "$n" -gt "$MAX" ]; then
    echo "❌ $f has $n lines (max $MAX)"
    fail=1
  fi
done < <(git ls-files '*.ts' '*.tsx' '*.py' '*.sql' | grep -v 'types/api.ts')
exit $fail
