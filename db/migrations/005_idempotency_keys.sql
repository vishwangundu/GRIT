-- 005: Idempotency-Key support for POST booking and POST outcome (PRD section 10).
create table idempotency_keys (
  user_id     uuid not null references profiles(id) on delete cascade,
  key         text not null,
  scope       text not null,
  status_code smallint not null,
  response    jsonb not null,
  created_at  timestamptz not null default now(),
  primary key (user_id, scope, key)
);
create index idempotency_keys_created_idx on idempotency_keys (created_at);
alter table idempotency_keys enable row level security;
