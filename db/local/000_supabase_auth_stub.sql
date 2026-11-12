-- LOCAL ONLY. Mimics the parts of Supabase's auth schema that our migrations reference,
-- so migrations and tests run on plain Postgres. Never run this on Supabase.
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key, email text);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;
