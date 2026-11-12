import type { ReactElement } from 'react';

import { Field, INPUT_CLASS } from '@/components/ui/Field';
import type { ResultDraft } from '@/lib/result-form';

interface Props {
  draft: ResultDraft;
  minChars: number;
  error?: string;
  onChange: (patch: Partial<ResultDraft>) => void;
}

export function FeedbackFields({
  draft,
  minChars,
  error,
  onChange,
}: Readonly<Props>): ReactElement {
  const isRequired = draft.result === 'fail' || draft.result === 'retake_later';
  const rule = isRequired ? ` At least ${String(minChars)} characters.` : '';
  return (
    <>
      <Field
        id="feedback"
        label={isRequired ? 'Feedback to student (required)' : 'Feedback to student (optional)'}
        hint={`Shown to the student word for word.${rule}`}
        error={error}
      >
        <textarea
          id="feedback"
          rows={3}
          value={draft.feedback}
          aria-describedby="feedback-hint"
          onChange={(e) => {
            onChange({ feedback: e.target.value });
          }}
          className={INPUT_CLASS}
        />
      </Field>
      <Field id="internal-notes" label="Internal note (admins only)">
        <textarea
          id="internal-notes"
          rows={2}
          value={draft.internalNotes}
          onChange={(e) => {
            onChange({ internalNotes: e.target.value });
          }}
          className={INPUT_CLASS}
        />
      </Field>
    </>
  );
}
