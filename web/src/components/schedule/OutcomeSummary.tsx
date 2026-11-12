import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { Chip } from '@/components/ui/Chip';
import { RESULT_LABELS, RUBRIC_LABELS } from '@/lib/labels';
import { formatDate, formatDateTime } from '@/lib/time';
import type { InterviewerOutcome } from '@/types/models';

interface Props {
  outcome: InterviewerOutcome;
  onEdit: () => void;
}

export function OutcomeSummary({ outcome, onEdit }: Readonly<Props>): ReactElement {
  const label = RESULT_LABELS[outcome.result];
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Chip tone={label.tone}>{label.label}</Chip>
        <span className="text-muted">Recorded {formatDateTime(outcome.recorded_at)}</span>
      </div>
      {outcome.rubric ? (
        <dl className="grid grid-cols-2 gap-1">
          {Object.entries(outcome.rubric).map(([area, score]) => (
            <div key={area} className="contents">
              <dt className="text-muted">{RUBRIC_LABELS[area] ?? area}</dt>
              <dd className="font-semibold">{score} / 4</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {outcome.feedback_to_student ? <p>Feedback: “{outcome.feedback_to_student}”</p> : null}
      {outcome.internal_notes ? (
        <p className="text-muted">Internal: {outcome.internal_notes}</p>
      ) : null}
      {outcome.retake_after ? <p>Rebook from {formatDate(outcome.retake_after)}</p> : null}
      {outcome.can_edit ? (
        <div className="flex items-center justify-between gap-2">
          <span className="text-muted">
            Editable until {formatDateTime(outcome.editable_until)}
          </span>
          <Button variant="secondary" onClick={onEdit}>
            Edit result
          </Button>
        </div>
      ) : (
        <Chip tone="neutral">Locked</Chip>
      )}
    </div>
  );
}
