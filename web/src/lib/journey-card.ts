/** Maps a journey's effective_state to the interview card (PRD FR-S1 card table). */
import type { Tone } from '@/lib/tones';
import type { BookingView, JourneyCard, JourneyState, OutcomeView } from '@/types/models';

export type CardKind =
  | 'skills_left'
  | 'ready'
  | 'ticket'
  | 'live'
  | 'result_pending'
  | 'passed'
  | 'retake'
  | 'failed'
  | 'locked'
  | 'under_review'
  | 'nullified';

export interface CardSpec {
  kind: CardKind;
  tone: Tone;
  title: string;
}

function readyTitle(journey: JourneyCard, last: OutcomeView | null): string {
  if (journey.priority) return 'Pick a new interview slot';
  if (last && last.result !== 'pass') return 'Book your retake / next attempt';
  return 'You’re interview-ready';
}

function awaitingCard(booking: BookingView | null, now: Date): CardSpec {
  const isLive = booking !== null && now < new Date(booking.end_at);
  return isLive
    ? { kind: 'live', tone: 'info', title: 'Your interview is happening now' }
    : { kind: 'result_pending', tone: 'info', title: 'Interview done. Your result is on its way' };
}

interface CardContext {
  badge: string;
  journey: JourneyCard;
  booking: BookingView | null;
  last: OutcomeView | null;
  now: Date;
}

/** One builder per state; the Record type makes the mapping exhaustive at compile time. */
const BUILDERS: Record<JourneyState, (ctx: CardContext) => CardSpec> = {
  not_eligible: () => ({
    kind: 'skills_left',
    tone: 'neutral',
    title: 'Skills left for this badge',
  }),
  eligible: ({ journey, last }) => ({
    kind: 'ready',
    tone: 'info',
    title: readyTitle(journey, last),
  }),
  booked: () => ({ kind: 'ticket', tone: 'info', title: 'Your interview is booked' }),
  awaiting_result: ({ booking, now }) => awaitingCard(booking, now),
  passed: ({ badge }) => ({ kind: 'passed', tone: 'success', title: `${badge} Badge unlocked` }),
  retake_later: ({ badge }) => ({
    kind: 'retake',
    tone: 'warning',
    title: `One more round needed for your ${badge} interview`,
  }),
  failed: ({ badge, last }) => ({
    kind: 'failed',
    tone: 'danger',
    title:
      last?.result === 'no_show'
        ? 'You missed your interview'
        : `You didn’t clear the ${badge} interview this time`,
  }),
  locked: ({ badge }) => ({
    kind: 'locked',
    tone: 'danger',
    title: `Your ${badge} interview attempts are used up`,
  }),
  under_review: ({ badge }) => ({
    kind: 'under_review',
    tone: 'review',
    title: `Your ${badge} Badge is under review`,
  }),
  nullified: ({ badge }) => ({
    kind: 'nullified',
    tone: 'danger',
    title: `Your ${badge} Badge has been withdrawn`,
  }),
};

export function cardFor(
  journey: JourneyCard,
  booking: BookingView | null,
  last: OutcomeView | null,
  now: Date,
): CardSpec {
  const build = BUILDERS[journey.effective_state];
  return build({ badge: journey.badge.name, journey, booking, last, now });
}
