-- 002_rls.sql (FastAPI uses the service role and bypasses RLS; these protect direct anon-key access)
alter table profiles             enable row level security;
alter table students             enable row level security;
alter table interviewers         enable row level security;
alter table interview_journeys   enable row level security;
alter table bookings             enable row level security;
alter table slots                enable row level security;
alter table availability_windows enable row level security;
alter table interview_outcomes   enable row level security;
alter table badge_awards         enable row level security;
alter table malpractice_flags    enable row level security;
alter table journey_events       enable row level security;
alter table notifications        enable row level security;

create policy own_profile       on profiles           for select using (id = auth.uid());
create policy own_student       on students           for select using (id = auth.uid());
create policy own_journeys      on interview_journeys for select using (student_id = auth.uid());
create policy own_bookings      on bookings           for select using (student_id = auth.uid());
create policy own_notifications on notifications      for select using (user_id = auth.uid());
create policy read_own_notif    on notifications      for update using (user_id = auth.uid())
  with check (user_id = auth.uid());
-- No insert/update/delete policies elsewhere: all writes go through FastAPI.
-- interview_outcomes.internal_notes is never exposed to students: FastAPI student endpoints
-- select only safe columns.
