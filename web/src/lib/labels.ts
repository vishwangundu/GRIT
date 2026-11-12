/** Human labels and tones for API enums. */
import type { Tone } from '@/lib/tones';
import type { Chip, NotBookedRow, OutcomeResult } from '@/types/models';

export const CHIP_LABELS: Record<Chip, { label: string; tone: Tone }> = {
  open: { label: 'Open', tone: 'neutral' },
  upcoming: { label: 'Upcoming', tone: 'info' },
  live_now: { label: 'Live now', tone: 'success' },
  record_result: { label: 'Record result', tone: 'warning' },
  result_overdue: { label: 'Result overdue', tone: 'danger' },
  passed: { label: 'Passed', tone: 'success' },
  failed: { label: 'Failed', tone: 'danger' },
  retake_later: { label: 'Retake later', tone: 'warning' },
  no_show: { label: 'No-show', tone: 'danger' },
  blocked: { label: 'Blocked', tone: 'neutral' },
  cancelled: { label: 'Cancelled', tone: 'neutral' },
};

export const RESULT_LABELS: Record<OutcomeResult, { label: string; tone: Tone }> = {
  pass: { label: 'Pass', tone: 'success' },
  fail: { label: 'Fail', tone: 'danger' },
  retake_later: { label: 'Retake later', tone: 'warning' },
  no_show: { label: 'Didn’t join', tone: 'danger' },
};

type WaitStatus = NotBookedRow['status'];

export const WAIT_LABELS: Record<WaitStatus, { label: string; tone: Tone }> = {
  not_booked: { label: 'Not booked', tone: 'neutral' },
  can_rebook: { label: 'Can rebook', tone: 'info' },
  needs_rebooking: { label: 'Needs rebooking', tone: 'warning' },
  retake_until: { label: 'Retake until', tone: 'warning' },
  cooldown_until: { label: 'Cooldown until', tone: 'danger' },
};

export const RUBRIC_LABELS: Record<string, string> = {
  problem_solving: 'Problem solving',
  product_thinking: 'Product thinking',
  code_walkthrough: 'Code walkthrough',
  communication: 'Communication',
};

export const STATE_LABELS: Record<string, string> = {
  not_eligible: 'Not eligible',
  eligible: 'Eligible',
  booked: 'Booked',
  awaiting_result: 'Awaiting result',
  retake_later: 'Retake later',
  failed: 'Failed',
  locked: 'Locked',
  passed: 'Passed',
  under_review: 'Under review',
  nullified: 'Nullified',
};

export function stateLabel(state: string): string {
  return STATE_LABELS[state] ?? state;
}

export function plural(count: number, word: string): string {
  return `${String(count)} ${word}${count === 1 ? '' : 's'}`;
}
