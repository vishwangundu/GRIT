import { describe, expect, it } from 'vitest';

import { type ResultDraft, toPayload, validateDraft } from './result-form';
import type { Rules } from '@/types/models';

const rules = {
  rubric_areas: ['problem_solving', 'product_thinking', 'code_walkthrough', 'communication'],
  rubric_min: 1,
  rubric_max: 4,
  feedback_min_chars: 15,
} as Rules;

const fullRubric = {
  problem_solving: 3,
  product_thinking: 2,
  code_walkthrough: 2,
  communication: 3,
};

function draft(overrides: Partial<ResultDraft>): ResultDraft {
  return {
    result: 'pass',
    rubric: fullRubric,
    feedback: '',
    internalNotes: '',
    retakeDate: '',
    ...overrides,
  };
}

describe('validateDraft', () => {
  it('requires a result', () => {
    expect(validateDraft(draft({ result: null }), rules, '2026-11-19')).toEqual({
      result: 'Choose a result.',
    });
  });

  it('requires every rubric area except for no-shows', () => {
    const partial = draft({ rubric: { problem_solving: 3 } });
    expect(validateDraft(partial, rules, '2026-11-19').rubric).toBeDefined();
    expect(validateDraft({ ...partial, result: 'no_show' }, rules, '2026-11-19')).toEqual({});
  });

  it('requires 15 characters of feedback for fail and retake', () => {
    expect(
      validateDraft(draft({ result: 'fail', feedback: 'too short' }), rules, '2026-11-19').feedback,
    ).toBeDefined();
    expect(validateDraft(draft({ result: 'pass' }), rules, '2026-11-19')).toEqual({});
  });

  it('requires a future retake date', () => {
    const retake = draft({
      result: 'retake_later',
      feedback: 'Walk me through testing.',
      retakeDate: '2026-11-19',
    });
    expect(validateDraft(retake, rules, '2026-11-19').retakeDate).toBeDefined();
    expect(validateDraft({ ...retake, retakeDate: '2026-11-22' }, rules, '2026-11-19')).toEqual({});
  });
});

describe('toPayload', () => {
  it('drops the rubric for no-shows and the date for non-retakes', () => {
    expect(toPayload(draft({ result: 'no_show', retakeDate: '2026-11-22' }), rules)).toMatchObject({
      result: 'no_show',
      rubric: null,
      retake_after: null,
    });
  });
});
