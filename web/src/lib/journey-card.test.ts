import { describe, expect, it } from 'vitest';

import { cardFor } from './journey-card';
import type { BookingView, JourneyCard, JourneyState, OutcomeView } from '@/types/models';

function journey(state: JourneyState, priority = false): JourneyCard {
  return {
    id: 'j1',
    badge: { id: 1, name: 'Novice', track: 'AI Product Mastery', level_order: 1 },
    state,
    effective_state: state,
    priority,
    attempts_used: 0,
    attempts_left: 3,
    next_bookable_at: null,
    eligible_at: null,
  };
}

const booking: BookingView = {
  booking_id: 'b1',
  start_at: '2026-11-19T11:00:00Z',
  end_at: '2026-11-19T11:30:00Z',
  interviewer_name: 'Priya Sharma',
  reschedules_left: 2,
  can_change: false,
  join_opens_at: '2026-11-19T10:50:00Z',
  is_join_open: true,
  meeting_link: 'https://meet.google.com/x',
};

function outcome(result: OutcomeView['result']): OutcomeView {
  return { result, feedback_to_student: '', rubric: null, recorded_at: '', retake_after: null };
}

describe('cardFor', () => {
  it.each<[JourneyState, string, string]>([
    ['not_eligible', 'skills_left', 'neutral'],
    ['eligible', 'ready', 'info'],
    ['booked', 'ticket', 'info'],
    ['passed', 'passed', 'success'],
    ['retake_later', 'retake', 'warning'],
    ['failed', 'failed', 'danger'],
    ['locked', 'locked', 'danger'],
    ['under_review', 'under_review', 'review'],
    ['nullified', 'nullified', 'danger'],
  ])('maps %s to the %s card', (state, kind, tone) => {
    const card = cardFor(journey(state), null, null, new Date());
    expect(card.kind).toBe(kind);
    expect(card.tone).toBe(tone);
  });

  it('asks priority students to pick a new slot', () => {
    expect(cardFor(journey('eligible', true), null, null, new Date()).title).toBe(
      'Pick a new interview slot',
    );
  });

  it('offers a retake after a non-pass outcome', () => {
    expect(cardFor(journey('eligible'), null, outcome('fail'), new Date()).title).toBe(
      'Book your retake / next attempt',
    );
  });

  it('shows live during the slot and result pending after it', () => {
    const during = cardFor(
      journey('awaiting_result'),
      booking,
      null,
      new Date('2026-11-19T11:10:00Z'),
    );
    const after = cardFor(
      journey('awaiting_result'),
      booking,
      null,
      new Date('2026-11-19T12:00:00Z'),
    );
    expect(during.title).toBe('Your interview is happening now');
    expect(after.title).toBe('Interview done. Your result is on its way');
  });

  it('uses the no-show wording when the student did not join', () => {
    expect(cardFor(journey('failed'), null, outcome('no_show'), new Date()).title).toBe(
      'You missed your interview',
    );
  });
});
