-- 001_schema.sql
create extension if not exists btree_gist;
create extension if not exists pgcrypto;

-- identity
create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  role        text not null check (role in ('student','interviewer','admin')),
  full_name   text not null,
  email       text not null unique,
  created_at  timestamptz not null default now()
);

create table students (
  id      uuid primary key references profiles(id) on delete cascade,
  campus  text not null,
  batch   text not null,
  miles   integer not null default 0 check (miles >= 0)
);

create table interviewers (
  id        uuid primary key references profiles(id) on delete cascade,
  campus    text,
  daily_cap integer not null default 8,
  active    boolean not null default true
);

-- catalogue
create table tracks (id serial primary key, name text not null unique);

create table badges (
  id                serial primary key,
  track_id          integer not null references tracks(id),
  level             text not null check (level in
                      ('novice','specialist','expert','master','grand_master')),
  level_order       smallint not null check (level_order between 1 and 5),
  interview_minutes smallint not null default 30,
  unique (track_id, level)
);

create table skills (id serial primary key, name text not null unique);

create table badge_skill_requirements (
  badge_id  integer references badges(id),
  skill_id  integer references skills(id),
  min_level smallint not null check (min_level between 1 and 4),
  primary key (badge_id, skill_id)
);

create table student_skill_levels (
  student_id uuid references students(id) on delete cascade,
  skill_id   integer references skills(id),
  level      smallint not null check (level between 1 and 4),
  status     text not null default 'cleared' check (status in ('cleared','revoked')),
  cleared_at timestamptz not null default now(),
  primary key (student_id, skill_id, level)
);

create table interviewer_badges (
  interviewer_id uuid references interviewers(id) on delete cascade,
  badge_id       integer references badges(id),
  primary key (interviewer_id, badge_id)
);

-- availability and slots
create table availability_windows (
  id             uuid primary key default gen_random_uuid(),
  interviewer_id uuid not null references interviewers(id),
  starts_at      timestamptz not null,
  ends_at        timestamptz not null,
  slot_minutes   smallint not null default 30,
  deleted_at     timestamptz,
  created_at     timestamptz not null default now(),
  check (ends_at > starts_at),
  exclude using gist (interviewer_id with =, tstzrange(starts_at, ends_at) with &&)
    where (deleted_at is null)
);

create table slots (
  id             uuid primary key default gen_random_uuid(),
  window_id      uuid not null references availability_windows(id),
  interviewer_id uuid not null references interviewers(id),
  start_at       timestamptz not null,
  end_at         timestamptz not null,
  status         text not null default 'open' check (status in
                   ('open','booked','blocked','cancelled')),
  updated_at     timestamptz not null default now(),
  check (end_at > start_at),
  unique (interviewer_id, start_at)
);
create index slots_open_idx on slots (start_at) where status = 'open';

-- journeys, bookings, outcomes
create table interview_journeys (
  id                uuid primary key default gen_random_uuid(),
  student_id        uuid not null references students(id) on delete cascade,
  badge_id          integer not null references badges(id),
  state             text not null default 'not_eligible' check (state in
    ('not_eligible','eligible','booked','awaiting_result','retake_later','failed',
     'locked','passed','under_review','nullified')),
  eligible_at       timestamptz,
  attempts_used     smallint not null default 0 check (attempts_used between 0 and 3),
  next_bookable_at  timestamptz,
  active_booking_id uuid,
  priority          boolean not null default false,
  last_nudged_at    timestamptz,
  updated_at        timestamptz not null default now(),
  unique (student_id, badge_id)
);
create index journeys_badge_state_idx on interview_journeys (badge_id, state);

create table bookings (
  id               uuid primary key default gen_random_uuid(),
  journey_id       uuid not null references interview_journeys(id),
  slot_id          uuid not null references slots(id),
  student_id       uuid not null references students(id),
  status           text not null default 'confirmed' check (status in
    ('confirmed','rescheduled','cancelled_by_student','cancelled_by_interviewer',
     'cancelled_by_system','completed','no_show')),
  meeting_link     text,
  reschedule_count smallint not null default 0 check (reschedule_count between 0 and 2),
  cancel_reason    text,
  cancelled_by     uuid references profiles(id),
  booked_at        timestamptz not null default now(),
  cancelled_at     timestamptz
);
create unique index one_confirmed_per_slot    on bookings (slot_id)    where status = 'confirmed';
create unique index one_confirmed_per_journey on bookings (journey_id) where status = 'confirmed';

alter table interview_journeys
  add constraint journeys_active_booking_fk foreign key (active_booking_id) references bookings(id);

create table interview_outcomes (
  id                  uuid primary key default gen_random_uuid(),
  booking_id          uuid not null unique references bookings(id),
  journey_id          uuid not null references interview_journeys(id),
  interviewer_id      uuid not null references interviewers(id),
  result              text not null check (result in ('pass','fail','retake_later','no_show')),
  rubric              jsonb,
  feedback_to_student text not null default '',
  internal_notes      text not null default '',
  retake_after        timestamptz,
  attempt_counted     boolean not null,
  prev_snapshot       jsonb not null,          -- journey + miles before applying, used to undo on edit
  recorded_by         uuid not null references profiles(id),
  recorded_at         timestamptz not null default now(),
  locked_at           timestamptz not null,    -- recorded_at + 2 h
  edited_at           timestamptz,
  edit_note           text,
  check (result not in ('fail','retake_later') or length(trim(feedback_to_student)) >= 15),
  check (result <> 'retake_later' or retake_after is not null),
  check (result = 'no_show' or rubric is not null)
);
create index outcomes_journey_idx on interview_outcomes (journey_id);

create table badge_awards (
  id            uuid primary key default gen_random_uuid(),
  student_id    uuid not null references students(id),
  badge_id      integer not null references badges(id),
  outcome_id    uuid not null references interview_outcomes(id),
  miles_awarded integer not null default 500,
  status        text not null default 'active' check (status in
                  ('active','under_review','nullified')),
  awarded_at    timestamptz not null default now(),
  nullified_at  timestamptz,
  reason        text
);
create unique index one_live_award on badge_awards (student_id, badge_id)
  where status <> 'nullified';

create table malpractice_flags (
  id             uuid primary key default gen_random_uuid(),
  badge_award_id uuid not null references badge_awards(id),
  student_id     uuid not null references students(id),
  raised_by      uuid not null references profiles(id),
  source         text not null,
  evidence_url   text,
  status         text not null default 'open' check (status in ('open','upheld','dismissed')),
  decided_by     uuid references profiles(id),
  decided_at     timestamptz,
  decision_note  text,
  created_at     timestamptz not null default now()
);

-- audit and notifications
create table journey_events (
  id          bigserial primary key,
  journey_id  uuid not null references interview_journeys(id),
  from_state  text,
  to_state    text not null,
  actor_id    uuid references profiles(id),       -- null = system
  actor_role  text not null check (actor_role in ('student','interviewer','admin','system')),
  reason      text,
  meta        jsonb not null default '{}',
  created_at  timestamptz not null default now()
);
create index journey_events_journey_idx on journey_events (journey_id, created_at desc);

create or replace function forbid_change() returns trigger language plpgsql as $$
begin raise exception 'journey_events is append-only'; end $$;
create trigger journey_events_append_only before update or delete on journey_events
  for each row execute function forbid_change();

create table notifications (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references profiles(id),
  template   text not null,
  title      text not null,
  body       text not null,
  tone       text not null default 'info' check (tone in
               ('info','success','warning','danger','review')),
  payload    jsonb not null default '{}',
  channel    text not null default 'in_app' check (channel in ('in_app','email','whatsapp')),
  created_at timestamptz not null default now(),
  read_at    timestamptz
);
create index notifications_user_idx on notifications (user_id, created_at desc);

-- effective state (read-time derivation)
create or replace view v_journey_effective as
select j.*,
  case
    when j.state = 'booked' and now() >= s.start_at then 'awaiting_result'
    when j.state in ('retake_later','failed') and j.next_bookable_at is not null
         and now() >= j.next_bookable_at then 'eligible'
    else j.state
  end as effective_state,
  b.id as booking_id, s.id as slot_id, s.start_at, s.end_at,
  s.interviewer_id, b.reschedule_count, b.meeting_link
from interview_journeys j
left join bookings b on b.id = j.active_booking_id
left join slots s    on s.id = b.slot_id;
