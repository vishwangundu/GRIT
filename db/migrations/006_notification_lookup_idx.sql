-- 006: lets the scheduler and nudges check "already sent?" cheaply (idempotent jobs).
create index notifications_template_booking_idx
  on notifications (template, (payload->>'booking_id'));
