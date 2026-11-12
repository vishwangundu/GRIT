'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { DIALOG_FOOTER } from '@/components/ui/Dialog';
import { InlineError } from '@/components/ui/StateView';
import { useResultForm } from '@/hooks/use-result-form';
import type { InterviewerOutcome, Rules } from '@/types/models';

import { FeedbackFields } from './FeedbackFields';
import { ResultChoice } from './ResultChoice';
import { RetakeDateField } from './RetakeDateField';
import { RubricInput } from './RubricInput';

interface Props {
  bookingId: string;
  rules: Rules;
  existing: InterviewerOutcome | null;
  onSaved: () => Promise<unknown>;
  onCancel?: () => void;
  editNote?: string | null;
  /** Pin Cancel / Save to the bottom of a scrolling dialog. */
  stickyActions?: boolean;
}

export function ResultForm(props: Readonly<Props>): ReactElement {
  const { bookingId, rules, existing, onSaved, onCancel, editNote = null } = props;
  const { stickyActions = false } = props;
  const form = useResultForm({ bookingId, rules, existing, editNote, onSaved });
  const { draft, errors, update } = form;
  return (
    <form
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        void form.submit();
      }}
      className="flex flex-col gap-4"
    >
      <ResultChoice
        value={draft.result}
        onChange={(result) => {
          update({ result });
        }}
        error={errors.result}
      />
      {draft.result === 'no_show' ? null : (
        <RubricInput
          areas={rules.rubric_areas}
          min={rules.rubric_min}
          max={rules.rubric_max}
          value={draft.rubric}
          onChange={(area, score) => {
            update({ rubric: { ...draft.rubric, [area]: score } });
          }}
          error={errors.rubric}
        />
      )}
      {draft.result === 'retake_later' ? (
        <RetakeDateField
          value={draft.retakeDate}
          error={errors.retakeDate}
          onChange={(retakeDate) => {
            update({ retakeDate });
          }}
        />
      ) : null}
      <FeedbackFields
        draft={draft}
        minChars={rules.feedback_min_chars}
        error={errors.feedback}
        onChange={update}
      />
      <InlineError message={form.serverError} />
      <FormButtons
        isEdit={existing !== null}
        isBusy={form.isBusy}
        isSticky={stickyActions}
        onCancel={onCancel}
      />
    </form>
  );
}

function FormButtons(
  props: Readonly<{ isEdit: boolean; isBusy: boolean; isSticky: boolean; onCancel?: () => void }>,
): ReactElement {
  return (
    <div className={`flex justify-end gap-2 ${props.isSticky ? DIALOG_FOOTER : ''}`}>
      {props.onCancel ? (
        <Button variant="secondary" onClick={props.onCancel}>
          Cancel
        </Button>
      ) : null}
      <Button type="submit" isBusy={props.isBusy}>
        {props.isEdit ? 'Save changes' : 'Submit result'}
      </Button>
    </div>
  );
}
