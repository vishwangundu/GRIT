# Coding Standards: GRIT Interview Scheduling

Stack: Next.js (App Router, TypeScript) · FastAPI (Python 3.11) · Supabase Postgres + Auth

These rules are mandatory for every file, whether written by hand or by an AI tool. Put this file in the repo root and also copy it into your AI tool's rules (`.cursor/rules/standards.mdc`, `CLAUDE.md`, or the project instructions in Lovable/Bolt) so generated code follows it.

---

## 1. Hard limits (CI fails if broken)

| Item | Limit | Enforced by |
| --- | --- | --- |
| Lines per file (any language) | **500 max** (blank lines and comments excluded) | ESLint `max-lines`, `scripts/check-file-size.sh`, Pylint `max-module-lines` |
| Lines per function (TS) | 60 max | ESLint `max-lines-per-function` |
| Statements per function (Python) | 40 max | Ruff `PLR0915` |
| Cyclomatic complexity | 10 max | ESLint `complexity`, Ruff `C901` |
| Cognitive complexity | 15 max | SonarQube S3776, `sonarjs/cognitive-complexity` |
| Nesting depth | 3 max | ESLint `max-depth` |
| Function parameters | 4 max (TS), 5 max (Python) — use an object / Pydantic model beyond that | ESLint `max-params`, Ruff `PLR0913` |
| Line length | 100 characters | Prettier, Ruff |
| Duplicated code | 3% max on new code | SonarQube quality gate |
| `any` in TypeScript | 0 | ESLint `no-explicit-any` |
| `# type: ignore` / `@ts-ignore` | 0 (use `@ts-expect-error` with a reason only if unavoidable) | ESLint, review |
| Secrets in code | 0 | SonarQube, gitleaks |

## 2. Target sizes (split the file when you pass these)

| File type | Target max lines |
| --- | --- |
| `page.tsx` (Next.js route) | 150 |
| React component | 200 |
| Custom hook | 100 |
| Utility module (`lib/*.ts`) | 150 |
| FastAPI router file | 250 |
| FastAPI service file | 300 |
| Pydantic schema file | 200 |
| Test file | 500 |
| SQL migration | one concern per file, no limit |

When a file grows past its target: extract sub-components, move logic into a hook or service, or split by feature. Never "fix" the limit by cramming code onto fewer lines.

---

## 3. Project structure

```text
/web                              Next.js
  src/app/(auth)/login/page.tsx
  src/app/student/...             student routes
  src/app/interviewer/...         interviewer routes
  src/app/admin/...               admin routes
  src/components/ui/              generic UI (Button, Chip, Dialog)
  src/components/<feature>/       feature components (booking/, schedule/, tracker/)
  src/hooks/                      useDashboard, useSlots ...
  src/lib/api.ts                  the only place that calls FastAPI
  src/lib/time.ts                 the only place that converts UTC <-> IST
  src/lib/supabase/               client + server Supabase helpers
  src/types/api.ts                types generated from FastAPI OpenAPI
/api                              FastAPI
  app/main.py
  app/core/config.py              settings from env (pydantic-settings)
  app/core/rules.py               business constants (6 h, 14 d, 2 reschedules ...)
  app/core/errors.py              AppError + exception handlers
  app/deps/auth.py                JWT verify, require_role()
  app/db/session.py               asyncpg / SQLAlchemy engine
  app/routers/                    student.py, interviewer.py, admin.py, internal.py
  app/services/                   journey.py, booking.py, outcome.py, notify.py
  app/schemas/                    Pydantic request/response models
  app/repositories/               SQL queries only
  tests/
/db/migrations                    001_schema.sql, 002_rls.sql ...
/scripts/check-file-size.sh
```

Layer rules:

- **Next.js components never call `fetch` directly.** All API calls go through `src/lib/api.ts`.
- **FastAPI routers are thin:** parse input, call one service function, return a schema. No SQL and no business rules in routers.
- **Services hold business rules** and the state machine. Services call repositories.
- **Repositories hold SQL only.** No business decisions.
- **Constants live in `rules.py`** (backend) and are exposed to the frontend via the API, never hard-coded twice.

---

## 4. TypeScript rules

### 4.1 `tsconfig.json` (required flags)

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "forceConsistentCasingInFileNames": true,
    "useUnknownInCatchVariables": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

### 4.2 Rules

1. No `any`. Use `unknown` and narrow it, or a proper type.
2. Exported functions and components declare their return type.
3. No non-null assertions (`value!`). Handle `null` / `undefined` explicitly.
4. Use `type` imports: `import type { Booking } from '@/types/api'`.
5. API types are generated from FastAPI's OpenAPI schema (`npx openapi-typescript $API_URL/openapi.json -o src/types/api.ts`), never hand-written duplicates.
6. Validate untrusted input (forms, URL params) with **zod** before use.
7. Model states as string-literal unions, not loose strings:
   `type JourneyState = 'not_eligible' | 'eligible' | 'booked' | ...`
8. Use exhaustive `switch` on unions with a `never` check in `default`.
9. No `enum`; use `as const` objects or literal unions.
10. Prefer `const`; never `var`. No reassigned parameters.
11. Async functions are always awaited or explicitly handled (`no-floating-promises`).
12. Dates: store and pass ISO UTC strings; format to IST only in `lib/time.ts` using `Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata' })`.

### 4.3 Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Components, types | PascalCase | `InterviewCard`, `JourneyState` |
| Functions, variables | camelCase | `bookSlot`, `effectiveState` |
| Constants | UPPER_SNAKE_CASE | `RESCHEDULE_MAX` |
| Component files | PascalCase.tsx | `InterviewCard.tsx` |
| Other files | kebab-case.ts | `use-dashboard.ts` |
| Booleans | is/has/can prefix | `isOverdue`, `canReschedule` |

---

## 5. React / Next.js rules

1. Server Components by default; add `'use client'` only for state, effects or event handlers.
2. One component per file. Max 200 lines (see section 2).
3. No business logic in components: derive display state from API data with small pure helpers in `lib/`.
4. Every data view handles **loading, empty, error** states explicitly.
5. Never trust the client for permissions; hide UI by role but rely on FastAPI to enforce.
6. No inline styles except dynamic values; use Tailwind or CSS modules.
7. Accessibility: every input has a label, buttons are `<button>`, images have `alt`, visible focus ring, colour is never the only signal.
8. Lists use stable `key` (ids, never array index).
9. No `useEffect` for data fetching in client components; use a hook with SWR/React Query or server fetch.
10. Keep `page.tsx` as composition only: fetch, then render feature components.

---

## 6. ESLint configuration

Install:

```bash
npm i -D eslint @eslint/js typescript-eslint eslint-plugin-sonarjs \
  eslint-plugin-react-hooks eslint-plugin-jsx-a11y @next/eslint-plugin-next \
  prettier eslint-config-prettier
```

`web/eslint.config.mjs`:

```js
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import sonarjs from 'eslint-plugin-sonarjs';
import reactHooks from 'eslint-plugin-react-hooks';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import nextPlugin from '@next/eslint-plugin-next';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['.next/**', 'node_modules/**', 'src/types/api.ts', 'coverage/**'] },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  sonarjs.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { 'react-hooks': reactHooks, '@next/next': nextPlugin },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs['core-web-vitals'].rules,

      // size and complexity
      'max-lines': ['error', { max: 500, skipBlankLines: true, skipComments: true }],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
      complexity: ['error', 10],
      'max-depth': ['error', 3],
      'max-params': ['error', 4],
      'sonarjs/cognitive-complexity': ['error', 15],

      // correctness
      eqeqeq: ['error', 'always'],
      'no-console': ['error', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      'no-param-reassign': 'error',

      // typescript
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/explicit-module-boundary-types': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      '@typescript-eslint/no-magic-numbers': ['warn', {
        ignore: [-1, 0, 1, 2], ignoreArrayIndexes: true, ignoreEnums: true,
        ignoreTypeIndexes: true, ignoreReadonlyClassProperties: true,
      }],
    },
  },
  {
    files: ['**/*.test.ts', '**/*.test.tsx'],
    rules: { 'max-lines-per-function': 'off', '@typescript-eslint/no-magic-numbers': 'off' },
  },
  prettier,
);
```

`web/.prettierrc`:

```json
{ "printWidth": 100, "singleQuote": true, "semi": true, "trailingComma": "all" }
```

`web/package.json` scripts:

```json
{
  "scripts": {
    "lint": "eslint . --max-warnings=0",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write .",
    "test": "vitest run --coverage"
  }
}
```

---

## 7. Python / FastAPI rules

### 7.1 Rules

1. Type hints on every function, parameter and return. `mypy --strict` passes.
2. Request and response bodies are Pydantic models in `app/schemas/`. Never return raw dicts or ORM rows.
3. All SQL is parameterised. Never build SQL with f-strings or `%` formatting.
4. Every state-changing service runs in one transaction and locks the journey row (`SELECT ... FOR UPDATE`).
5. Raise `AppError(code, http_status, message)`; one global handler formats `{"error": {"code", "message"}}`. No bare `except:`; never swallow exceptions.
6. Business constants only in `app/core/rules.py`. No magic numbers in services.
7. Config only via `pydantic-settings` from environment variables.
8. Async all the way: `async def` routes and DB calls; no blocking calls inside them.
9. Datetimes are timezone-aware UTC (`datetime.now(UTC)`); IST via `zoneinfo.ZoneInfo("Asia/Kolkata")` only when parsing interviewer input.
10. Logging with the standard `logging` module in JSON format; no `print`.
11. Students' responses never include `internal_notes` or other students' data: use separate response schemas per role.

### 7.2 `api/pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
  "E", "W", "F",      # pycodestyle, pyflakes
  "I",                # isort
  "N",                # naming
  "UP",               # pyupgrade
  "B",                # bugbear
  "S",                # bandit security
  "C4", "C90",        # comprehensions, mccabe complexity
  "SIM", "RET", "ARG",
  "PL",               # pylint rules
  "PT",               # pytest style
  "DTZ",              # timezone-aware datetimes
  "T20",              # no print
  "RUF",
]
ignore = ["B008"]     # FastAPI Depends() in defaults

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5
max-branches = 10
max-returns = 5
max-statements = 40

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.pylint.format]
max-module-lines = 500

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--cov=app --cov-report=xml --cov-report=term-missing"
```

Commands:

```bash
ruff check . && ruff format --check . && mypy app && pytest
```

### 7.3 Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Modules, functions, variables | snake_case | `book_slot`, `effective_state` |
| Classes, Pydantic models | PascalCase | `BookingCreate`, `OutcomeResponse` |
| Constants | UPPER_SNAKE_CASE | `FAIL_COOLDOWN_DAYS` |
| Error codes | snake_case strings | `slot_taken`, `edit_window_closed` |

---

## 8. Database rules

1. Schema changes only through numbered files in `db/migrations/`. Never edit a migration that has been applied; add a new one.
2. Tables and columns in snake_case, plural table names.
3. Every table has a primary key; every relation has a foreign key.
4. Rules that must never break live in the DB too: `CHECK`, `UNIQUE`, partial unique indexes, exclusion constraints.
5. No `SELECT *` in application code; list columns.
6. Every foreign key and every column used in `WHERE` / `ORDER BY` on hot paths has an index.
7. RLS enabled on every table. Service-role key only on the FastAPI server, never in the browser.
8. `journey_events` is append-only (trigger blocks update/delete).

---

## 9. SonarQube / SonarCloud

Use **SonarCloud** (free for public GitHub repos) or a local SonarQube, plus **SonarQube for IDE (SonarLint)** in VS Code to see issues while coding.

`sonar-project.properties` (repo root):

```properties
sonar.projectKey=grit-interview-scheduling
sonar.projectName=GRIT Interview Scheduling
sonar.sources=web/src,api/app
sonar.tests=web/src,api/tests
sonar.test.inclusions=**/*.test.ts,**/*.test.tsx,api/tests/**
sonar.exclusions=**/node_modules/**,**/.next/**,web/src/types/api.ts,db/**
sonar.javascript.lcov.reportPaths=web/coverage/lcov.info
sonar.python.coverage.reportPaths=api/coverage.xml
sonar.python.version=3.11
sonar.sourceEncoding=UTF-8
```

### Quality gate (on new code)

| Metric | Condition |
| --- | --- |
| Reliability rating | A (0 bugs) |
| Security rating | A (0 vulnerabilities) |
| Security hotspots reviewed | 100% |
| Maintainability rating | A |
| Duplicated lines | ≤ 3% |
| Coverage | ≥ 70% (≥ 90% on `services/booking.py` and `services/outcome.py`) |
| Blocker / critical issues | 0 |

### Sonar rules to watch

| Rule | Meaning |
| --- | --- |
| S3776 | Cognitive complexity over 15: split the function |
| S1192 | Same string literal repeated 3+ times: make it a constant |
| S1135 / S1134 | `TODO` / `FIXME` left in code: resolve before merge |
| S125 | Commented-out code: delete it |
| S1481 / S1854 | Unused variable / dead store |
| S2068 / S6418 | Hard-coded password / secret |
| S3649 / S2077 | SQL built from user input |
| S4507 | Debug mode left on in production |
| S5332 | Insecure `http://` URLs |
| S6479 | Array index used as React `key` |

---

## 10. Security rules

1. No secrets, keys or passwords in code or Git history. Use `.env` files listed in `.gitignore`; commit only `.env.example`.
2. FastAPI verifies the Supabase JWT on every request and reads the role from `profiles`, never from the request body.
3. CORS allows only the deployed Vercel domain (and `localhost` in development).
4. Validate every input: Pydantic on the server, zod on the client.
5. Never log JWTs, passwords or full request bodies containing personal data.
6. Run `gitleaks detect` before pushing; `npm audit --omit=dev` and `pip-audit` show 0 high/critical issues.

---

## 11. Testing rules

| Layer | Tool | Must cover |
| --- | --- | --- |
| FastAPI services | pytest + pytest-asyncio | Every state transition in the PRD; booking race (two parallel requests on one slot → exactly one 201); reschedule limit; 12 h cutoff; outcome edit undo; 3rd fail → locked; uphold → Miles reversed |
| FastAPI routes | httpx `AsyncClient` | Role checks (student cannot call interviewer routes → 403), error shape |
| Frontend helpers | vitest | `lib/time.ts` IST formatting, state-to-card mapping |
| End to end (optional) | Playwright | Book → record Pass → student sees badge |

Test names describe behaviour: `test_second_booking_on_same_slot_returns_409`.

---

## 12. File-size check script

`scripts/check-file-size.sh` (runs in CI and pre-commit for every language):

```bash
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
```

---

## 13. Git and CI

1. Branches: `feat/<short-name>`, `fix/<short-name>`. No direct pushes to `main`.
2. Conventional commits: `feat: add booking endpoint`, `fix: handle slot_taken race`.
3. Pre-commit hooks: **husky + lint-staged** for `web` (eslint, prettier), **pre-commit** for `api` (ruff, mypy), plus `check-file-size.sh` and `gitleaks`.
4. GitHub Actions on every PR, in order: file-size check → lint → typecheck → tests with coverage → SonarCloud scan. Merge only when all pass.

---

## 14. Definition of done (per feature)

- [ ] Matches the PRD section it implements (states, rules, messages word for word)
- [ ] No file over 500 lines; components and services within target sizes
- [ ] `npm run lint`, `npm run typecheck`, `ruff`, `mypy` pass with 0 warnings
- [ ] Tests written for new service logic; coverage gate met
- [ ] SonarQube quality gate green; no new code smells above minor
- [ ] Loading, empty and error states handled in UI
- [ ] No secrets, no `console.log`, no `print`, no commented-out code, no TODOs
- [ ] Works at 360 px width and with keyboard only

---

## 15. Instructions for AI coding tools

Paste this block into your AI tool's rules:

```text
Follow CODING_STANDARDS.md strictly.
- Never create a file longer than 500 lines; split into smaller modules instead.
- React components ≤ 200 lines, functions ≤ 60 lines, complexity ≤ 10, nesting ≤ 3.
- TypeScript strict mode: no `any`, no non-null assertions, explicit return types on exports,
  type-only imports, exhaustive switches on union types.
- Frontend calls the backend only through src/lib/api.ts; IST formatting only in src/lib/time.ts.
- FastAPI: thin routers -> services (business rules) -> repositories (SQL only).
  Pydantic schemas for all I/O, parameterised SQL, one transaction per state change,
  constants only in app/core/rules.py, type hints everywhere (mypy --strict).
- Return errors as {"error": {"code", "message"}} using the codes in the PRD.
- Handle loading, empty and error states in every view.
- No secrets in code, no console.log/print, no commented-out code, no TODOs.
- After generating a file, check it against these limits before moving on.
```
