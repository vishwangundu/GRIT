# GRIT Interview Scheduling: Write-up

**Vishwan Gundu** · Live prototype: [grit-gules-phi.vercel.app](https://grit-gules-phi.vercel.app) (demo logins `admin@demo.grit`, `priya@demo.grit`, `aarav@demo.grit`; password `Grit@2026`)

I designed the feature around one idea: every student has **one interview journey per badge**, and that journey is always in exactly **one state**. Every screen (student, interviewer, interview team) reads the same state, so all three roles always see the same truth. All rules live in the backend API, and the database enforces the ones that matter when two people act at the same moment.

## 1. States

| State | What the student sees | Moves to | What moves it |
| --- | --- | --- | --- |
| **not_eligible** | Skills left for this badge | eligible | The last required skill is cleared (the skills service recomputes eligibility) |
| **eligible** | "You're interview-ready" + Book | booked | Student books a slot 6 h to 14 days ahead |
| **booked** | Ticket: date, time, interviewer, join link 10 min before | eligible · awaiting_result | Student or interviewer cancels (an interviewer cancel gives the student priority to rebook) · the slot's start time passes |
| **awaiting_result** | "Happening now", then "Your result is on its way" | passed · retake_later · failed · locked | Interviewer records Pass · Retake later · Fail or No-show · that failure was attempt 3 |
| **retake_later** | "One more round needed", bookable from a date | eligible | The retake date arrives (not counted as an attempt) |
| **failed** | "You didn't clear it this time", rebook date, attempts left | eligible | Cooldown ends: 14 days after a Fail, 7 days after a No-show |
| **locked** | "Your attempts are used up" | — | End state after 3 failed attempts |
| **passed** | "Badge unlocked", +500 Miles, Qualiflyer leaderboard | under_review | The team raises a malpractice flag |
| **under_review** | "Your badge is under review" (paused on leaderboard) | passed · nullified | The team dismisses the flag · upholds it |
| **nullified** | "Your badge has been withdrawn", Miles removed | — | End state |

Two moves depend only on time (booked → awaiting_result, and a cooldown ending back in eligible). I derive these when the data is read instead of running a job, so the screen is never out of date. An interviewer can edit a result for 2 hours; I restore the journey from a saved snapshot and reverse the Miles by the difference. Every move writes an audit event that can't be edited or deleted.

## 2. Edge cases and questions

**Cases I handle**

- **Two students click the same slot:** the database allows only one confirmed booking per slot (and one per journey). The second student sees "That slot was just taken. Pick another one."
- **Booking rules:** slots from 6 hours to 14 days ahead; cancel or reschedule until 12 hours before; at most 2 reschedules.
- **Interviewer can't make it:** they cancel with a reason and the student goes back to eligible with priority, or the team reassigns the booking to another free interviewer at the same time.
- **Overlapping availability:** the database rejects overlapping windows for the same interviewer; a window that has a booking can't be removed.
- **Bad or missing results:** a result can only be recorded after the interview starts, all 4 rubric areas must be scored 1–4, Fail and Retake need at least 15 characters of feedback, and a retake date must be in the future. Interviewers get reminders at 2 h and 20 h; the team sees it as overdue at 24 h.
- **No-show:** counts as an attempt with a 7-day cooldown. Retake later never counts.
- **Malpractice found after a Pass:** the badge goes under review first, so nothing is removed by mistake. Upholding removes the badge and its 500 Miles; dismissing restores it.
- **Double clicks and retries:** booking and result requests carry an idempotency key, so a repeated click doesn't create a second booking.
- **Time zones:** stored in UTC, always shown in IST.
- **Roles:** students self-register and are always created as students; interviewers and admins are added by the team. The API checks the role on every request.

**Assumptions**

- Interviews are 30 minutes, online, on a fixed Google Meet room per interviewer.
- 3 attempts per badge; a 14-day cooldown after a Fail.
- Eligibility comes from the existing skills service; students can't declare it themselves.
- An interviewer only interviews for the badges they are cleared for.

**Open questions**

- Who can unlock a locked journey, and after how long?
- Should a student be able to appeal a withdrawn badge in the app, or only by contacting the team?
- Do interviewers need a daily interview cap, or is their availability enough?

## 3. Data model

Postgres (Supabase), 19 tables. The journey row is the state machine; bookings, outcomes and awards hang off it.

| Table | Key fields | Rules in the schema |
| --- | --- | --- |
| **profiles** | id (= auth user), role, full_name, email | role is student, interviewer or admin |
| **students** / **interviewers** | campus, batch, miles / campus, meet_link, active | miles ≥ 0 |
| **badges**, **skills**, **badge_skill_requirements** | track, level 1–5; minimum skill level per badge | one badge per track and level |
| **student_skill_levels** | student, skill, level, status | filled by the skills service |
| **availability_windows** | interviewer, starts_at, ends_at, deleted_at | no overlapping live windows (exclusion constraint) |
| **slots** | window, start_at, end_at, status (open / booked / blocked / cancelled) | unique per interviewer and start time |
| **interview_journeys** | student, badge, state, attempts_used, next_bookable_at, active_booking_id, priority | one per student and badge; attempts 0–3 |
| **bookings** | journey, slot, status, meeting_link, reschedule_count, cancel_reason | one confirmed booking per slot and per journey; reschedules 0–2 |
| **interview_outcomes** | booking, result, rubric, feedback_to_student, internal_notes, retake_after, prev_snapshot, locked_at | one per booking; feedback ≥ 15 characters for Fail and Retake |
| **badge_awards** | student, badge, outcome, miles_awarded, status | one live award per student and badge |
| **malpractice_flags** | award, raised_by, evidence_url, status, decision_note | open / upheld / dismissed |
| **journey_events** | journey, from_state, to_state, actor, reason | append-only audit log |
| **notifications** | user, template, title, body, tone, read_at | in-app today; email and WhatsApp reserved |

A view (`v_journey_effective`) applies the time-based moves when data is read, and another (`v_leaderboard`) ranks Qualiflyers and Pre-Qualiflyers by Miles. Row-level security limits each role to its own rows.
