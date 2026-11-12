/** Client-side checks for the result form (FR-I3). FastAPI re-validates everything. */
import { z } from 'zod';

import type { OutcomeCreate, OutcomeResult, Rules } from '@/types/models';

export interface ResultDraft {
  result: OutcomeResult | null;
  rubric: Record<string, number | undefined>;
  feedback: string;
  internalNotes: string;
  retakeDate: string;
}

export type DraftErrors = Partial<Record<'result' | 'rubric' | 'feedback' | 'retakeDate', string>>;

const resultSchema = z.enum(['pass', 'fail', 'retake_later', 'no_show']);

export function validateDraft(draft: ResultDraft, rules: Rules, todayKey: string): DraftErrors {
  const errors: DraftErrors = {};
  const parsed = resultSchema.safeParse(draft.result);
  if (!parsed.success) return { result: 'Choose a result.' };
  const result = parsed.data;
  if (result !== 'no_show') {
    const scored = rules.rubric_areas.every((area) => {
      const score = draft.rubric[area];
      return score !== undefined && score >= rules.rubric_min && score <= rules.rubric_max;
    });
    if (!scored) errors.rubric = `Score all ${String(rules.rubric_areas.length)} areas.`;
  }
  const needsFeedback = result === 'fail' || result === 'retake_later';
  if (needsFeedback && draft.feedback.trim().length < rules.feedback_min_chars) {
    errors.feedback = `Write at least ${String(rules.feedback_min_chars)} characters for the student.`;
  }
  if (result === 'retake_later' && draft.retakeDate <= todayKey) {
    errors.retakeDate = 'Pick a date after today.';
  }
  return errors;
}

export function toPayload(draft: ResultDraft, rules: Rules): OutcomeCreate {
  const result = resultSchema.parse(draft.result);
  const rubric =
    result === 'no_show'
      ? null
      : Object.fromEntries(rules.rubric_areas.map((area) => [area, draft.rubric[area] ?? 0]));
  return {
    result,
    rubric,
    feedback_to_student: draft.feedback.trim(),
    internal_notes: draft.internalNotes.trim(),
    retake_after: result === 'retake_later' ? draft.retakeDate : null,
  };
}
