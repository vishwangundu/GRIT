-- 004: indexes for foreign keys and hot-path filters not covered by 001 (CODING_STANDARDS §8.6).
create index slots_window_idx          on slots (window_id);
create index slots_interviewer_day_idx on slots (interviewer_id, start_at);
create index bookings_journey_idx      on bookings (journey_id);
create index bookings_student_idx      on bookings (student_id);
create index outcomes_interviewer_idx  on interview_outcomes (interviewer_id);
create index awards_outcome_idx        on badge_awards (outcome_id);
create index flags_award_idx           on malpractice_flags (badge_award_id);
create index flags_student_idx         on malpractice_flags (student_id);
create index windows_interviewer_idx   on availability_windows (interviewer_id, starts_at)
  where deleted_at is null;
