# GRIT Interview Scheduling

Product spec: "PRD: GRIT Interview Scheduling" (state machine §3, endpoints §7, notification
copy §8, edge cases §9). Notification wording for `booked`, `pass` and `retake` must never change.

## Rules for AI coding tools

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

## Commands

- API checks (from `api/`): `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest`
- Tests need a throwaway Postgres: `TEST_DATABASE_URL=postgresql://postgres@localhost:55432/grit_test`.
  The test suite drops and recreates the `public` and `auth` schemas in that database.
- File-size gate: `scripts/check-file-size.sh`

## Layout notes

- `db/migrations/` runs in order on Supabase. `db/local/000_supabase_auth_stub.sql` fakes the
  Supabase `auth` schema for local Postgres only; never run it on Supabase.
- Services decide effective state in Python (`services/journey.py::effective_state`) using the same
  rules as the `v_journey_effective` view; keep the two in sync.

## Brand

- Only the frame follows grit.niatindia.com: the official crest + wordmark
  (`web/src/components/shell/Wordmark.tsx`), the dark pill nav, and the Familjen Grotesk / DM Sans
  type. Screens inside the app use a plain, light UI: `grit-panel` / `grit-tile` utilities,
  `border-line` borders, GRIT blue (`grit-blue-strong`) for primary actions and selection.
- Colour tokens live in `web/src/app/globals.css` (`@theme`) and tones in `lib/tones.ts`; don't use
  Tailwind's default palette. Use `-strong` accent shades for any text on colour (4.5:1 contrast).
