-- 007: leaderboard ranking. Qualiflyers hold a live badge award (active or under review);
-- a student whose badge is under review stays listed but is shown as paused.
create or replace view v_leaderboard as
with s as (
  select st.id, p.full_name, st.campus, st.miles,
    exists (select 1 from badge_awards a where a.student_id = st.id
            and a.status in ('active', 'under_review')) as is_qualiflyer,
    exists (select 1 from interview_journeys j where j.student_id = st.id
            and j.state = 'under_review') as is_paused,
    (select count(*) from badge_awards a where a.student_id = st.id
       and a.status in ('active', 'under_review'))::int as badge_count
  from students st join profiles p on p.id = st.id
)
select id, full_name, campus, miles, is_qualiflyer, is_paused, badge_count,
       (rank() over (partition by is_qualiflyer order by miles desc, full_name))::int as rank
from s;
