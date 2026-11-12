-- 003: fixed Google Meet room per interviewer (PRD §13: real Meet creation is out of scope).
-- Copied onto bookings.meeting_link at booking time.
alter table interviewers add column meet_link text;
