'use client';

import { useState } from 'react';

import { ApiError } from '@/lib/api';
import { editOutcome, recordOutcome } from '@/lib/endpoints/interviewer';
import { type DraftErrors, type ResultDraft, toPayload, validateDraft } from '@/lib/result-form';
import { addDays, istDateKey } from '@/lib/time';
import type { InterviewerOutcome, Rules } from '@/types/models';

interface Options {
  bookingId: string;
  rules: Rules;
  existing: InterviewerOutcome | null;
  editNote: string | null;
  onSaved: () => Promise<unknown>;
}

function retakeKey(retakeAfter: string | null, fallback: string): string {
  return retakeAfter ? istDateKey(new Date(retakeAfter)) : fallback;
}

function initialDraft(rules: Rules, existing: InterviewerOutcome | null): ResultDraft {
  const defaultRetake = addDays(istDateKey(), rules.retake_default_days);
  if (!existing) {
    return { result: null, rubric: {}, feedback: '', internalNotes: '', retakeDate: defaultRetake };
  }
  return {
    result: existing.result,
    rubric: existing.rubric ?? {},
    feedback: existing.feedback_to_student,
    internalNotes: existing.internal_notes,
    retakeDate: retakeKey(existing.retake_after, defaultRetake),
  };
}

export function useResultForm({ bookingId, rules, existing, editNote, onSaved }: Options): {
  draft: ResultDraft;
  errors: DraftErrors;
  serverError: string | null;
  isBusy: boolean;
  update: (patch: Partial<ResultDraft>) => void;
  submit: () => Promise<void>;
} {
  const [draft, setDraft] = useState<ResultDraft>(() => initialDraft(rules, existing));
  const [errors, setErrors] = useState<DraftErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function submit(): Promise<void> {
    const found = validateDraft(draft, rules, istDateKey());
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setIsBusy(true);
    setServerError(null);
    try {
      const payload = toPayload(draft, rules);
      if (existing) await editOutcome(bookingId, { ...payload, edit_note: editNote });
      else await recordOutcome(bookingId, payload);
      await onSaved();
    } catch (err: unknown) {
      setServerError(err instanceof ApiError ? err.message : 'Could not save. Try again.');
    } finally {
      setIsBusy(false);
    }
  }

  function update(patch: Partial<ResultDraft>): void {
    setDraft((current) => ({ ...current, ...patch }));
  }

  return { draft, errors, serverError, isBusy, update, submit };
}
