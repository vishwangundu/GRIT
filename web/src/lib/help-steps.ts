/** Local setup and test walkthrough shown by the Help dialog on the sign-in screen. */

export interface HelpStep {
  title: string;
  note?: string;
  commands: readonly string[];
}

export const HELP_STEPS: readonly HelpStep[] = [
  {
    title: 'Set up the database (once, on an empty database)',
    note: 'Run from the repo root. Fill in api/.env and web/.env.local first.',
    commands: [
      'set -a && . api/.env && set +a',
      'for f in db/migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"; done',
      'cd api && uv run python -m scripts.seed_catalogue',
    ],
  },
  {
    title: 'Start the API',
    note: 'Swagger: http://localhost:8000/docs',
    commands: ['cd api && uv sync && uv run uvicorn app.main:app --reload --port 8000'],
  },
  {
    title: 'Start the web app',
    note: 'In a second terminal. Then open http://localhost:3000',
    commands: ['cd web && npm ci && npm run dev'],
  },
  {
    title: 'Create test accounts',
    note:
      'Register each account at /register (every new account is a student), then run these ' +
      'from api/. Use a real mailbox: Supabase rejects domains like test.com, so use ' +
      'Gmail + aliases (you+admin@gmail.com). Sign out and back in after a role change.',
    commands: [
      'uv run python -m scripts.test_account you+admin@gmail.com admin',
      'uv run python -m scripts.test_account you+int@gmail.com interviewer',
      'uv run python -m scripts.test_account you+stu@gmail.com eligible',
    ],
  },
  {
    title: 'Or load the full demo data instead',
    note: 'Replaces all data with the demo accounts (<name>@demo.grit). Run from api/.',
    commands: ['uv run python -m scripts.seed'],
  },
];

export const HELP_FLOW: readonly string[] = [
  'Interviewer: Availability → add a window at least 6 hours from now.',
  'Student: Book → pick a slot → tick the checkbox → confirm. Check the ticket and Messages.',
  'Interviewer: Schedule → open the interview → record the result once it has ended.',
  'Student: Dashboard shows the result (Pass adds 500 Miles and the badge).',
  'Admin: Tracker → Not booked, Booked, Awaiting result and Results tabs.',
];
