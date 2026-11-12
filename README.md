# GRIT Interview Scheduling

Eligible GRIT students book a 30-minute Level Clearance Interview, interviewers publish
availability and record results, and the interview team tracks who has and hasn't booked.
Built from "PRD: GRIT Interview Scheduling" and [CODING_STANDARDS.md](CODING_STANDARDS.md).

| Part | Stack | Folder |
| --- | --- | --- |
| Web | Next.js 16 (App Router, TypeScript, Tailwind 4), Supabase Auth, SWR | [web/](web/) |
| API | FastAPI (Python 3.11), asyncpg; owns every rule and state change | [api/](api/) |
| Database | Supabase Postgres: constraints, effective-state view, RLS | [db/migrations/](db/migrations/) |

## Run it locally

You need Postgres 16 (with `btree_gist`), [uv](https://docs.astral.sh/uv/) and Node 22.

```bash
# 1. Database (plain Postgres: load the local auth stub first, then the migrations)
createdb grit_dev
psql -d grit_dev -f db/local/000_supabase_auth_stub.sql
for f in db/migrations/*.sql; do psql -d grit_dev -v ON_ERROR_STOP=1 -f "$f"; done

# 2. API
cd api
cp .env.example .env          # set DATABASE_URL, SUPABASE_JWT_SECRET, INTERNAL_API_KEY
uv sync
uv run python -m scripts.seed # demo data from PRD section 11
uv run uvicorn app.main:app --reload --port 8000   # Swagger at http://localhost:8000/docs

# 3. Web (needs a Supabase project for login, see below)
cd ../web
cp .env.example .env.local
npm ci && npm run dev
```

`db/local/000_supabase_auth_stub.sql` only fakes Supabase's `auth` schema for local Postgres.
**Never run it on Supabase.**

## Checks (what CI runs)

```bash
scripts/check-file-size.sh
cd api && uv run ruff check . && uv run ruff format --check . && uv run mypy app scripts \
  && TEST_DATABASE_URL=postgresql://postgres@localhost:5432/grit_test uv run pytest
cd web && npm run lint && npm run typecheck && npm test && npm run build
```

The API tests drop and recreate the schemas in `TEST_DATABASE_URL`, so point it at a
throwaway database. Install the git hooks with `pre-commit install`
([.pre-commit-config.yaml](.pre-commit-config.yaml)).

## Deploy

1. **Supabase.** Create a project. In the SQL editor run `db/migrations/001` to `007` in
   order (not the local stub). Under Authentication → Providers, keep Email enabled.
2. **API on Render.** New → Blueprint → this repo ([render.yaml](render.yaml)). Fill in:
   - `DATABASE_URL`: the **Session pooler** connection string (Supabase → Connect). The direct
     `db.<ref>.supabase.co` host is IPv6-only and Render can't reach it.
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
   - `SUPABASE_JWT_SECRET`: only if your project still uses the legacy HS256 secret. New
     projects sign tokens with asymmetric keys, which the API fetches from JWKS via
     `SUPABASE_URL`.
   - `CORS_ORIGINS`: your Vercel URL. `DEMO_USER_PASSWORD`: `Grit@2026` for the demo accounts.
3. **Seed.** From `api/` with the production env set: `uv run python -m scripts.seed`.
   It creates the demo users through the Supabase Admin API. To reset before recording:
   `curl -X POST -H "X-Internal-Key: $INTERNAL_API_KEY" https://<api>/api/v1/internal/demo/reset`.
4. **Web on Vercel.** Import the repo with Root Directory `web`. Set
   `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` and
   `NEXT_PUBLIC_API_URL=https://<api-host>/api/v1`.
5. **SonarCloud (optional).** Add the `SONAR_TOKEN` secret and set the repository variable
   `SONAR_ENABLED=true`.

## Demo path

Accounts are `<name>@demo.grit` (password `DEMO_USER_PASSWORD`). The path below was run end to
end in Chrome; screenshots are in [docs/screenshots/](docs/screenshots/).

1. `aarav` books a slot (dashboard → Book → confirm checkbox) and gets "Your interview is booked".
2. `priya` opens the "Results to record" banner, picks Sneha, and records Pass.
3. `sneha` sees the green unlock card, +500 Miles, 1 badge, Qualiflyer rank.
4. `admin` → Results tab → Flag malpractice → Uphold (with confirm).
5. `sneha` sees the withdrawal notice, Miles −500, 0 badges, back to Pre-Qualiflyer.

## Student sign-up

Students can create their own account at `/register` (name, email, campus, batch, password).
The browser signs up with Supabase Auth, then `POST /api/v1/register` creates the profile.
FastAPI always sets the role to **student**, whatever the request contains; interviewers and
admins are added by the interview team. Campuses and batches come from `app/core/rules.py`
through the public `GET /api/v1/registration-options`. If your Supabase project requires email
confirmation, the profile is created automatically on the student's first sign-in.

## Decisions worth knowing

- **Effective state** is derived at read time (`v_journey_effective`), and services apply the
  same rules in `services/journey.py`. A derived move is written, with a `system` audit event,
  the next time FastAPI changes that journey.
- **Outcome edits** restore the journey from `prev_snapshot` but reverse Pass Miles by delta,
  so Miles earned elsewhere in the meantime are kept. The old award is nullified, not deleted.
- **Meet links** use a fixed room per interviewer (`interviewers.meet_link`, migration 003),
  shown to the student only from 10 minutes before the start.
- **Reminders** run in-process every 60 minutes and are idempotent; an advisory lock keeps two
  API instances from sending the same reminder.
- **Sign-in screens** use the site's blue wash, slate borders and navy, with a world-landmarks
  skyline pinned to the bottom of the window (`web/public/skyline.png`: supplied artwork,
  background made transparent and tinted slate).
- **Look and feel:** the frame follows grit.niatindia.com (official NIAT crest and GRIT wordmark
  as inline SVG, dark pill nav, Familjen Grotesk and DM Sans). Screens inside the app use a plain,
  light UI with GRIT blue for actions and selection. Accent colours are deepened wherever they
  carry text, to keep 4.5:1 contrast.
