'use client';

import { type ReactElement, useState } from 'react';

import type { InterviewDetail, Rules } from '@/types/models';

import { OutcomeSummary } from './OutcomeSummary';
import { ResultForm } from './ResultForm';

interface Props {
  detail: InterviewDetail;
  rules: Rules;
  onSaved: () => Promise<unknown>;
}

/** Result form while recording or editing, otherwise the submitted summary (FR-I3, FR-I4). */
export function DetailResult({ detail, rules, onSaved }: Readonly<Props>): ReactElement {
  const [isEditing, setIsEditing] = useState(false);
  const outcome = detail.outcome;

  async function saved(): Promise<void> {
    setIsEditing(false);
    await onSaved();
  }

  if (detail.can_record) {
    return (
      <ResultForm bookingId={detail.booking_id} rules={rules} existing={null} onSaved={saved} />
    );
  }
  if (!outcome) {
    return <p className="text-sm text-muted">The result form opens when the interview starts.</p>;
  }
  if (isEditing) {
    return (
      <ResultForm
        bookingId={detail.booking_id}
        rules={rules}
        existing={outcome}
        onSaved={saved}
        onCancel={() => {
          setIsEditing(false);
        }}
      />
    );
  }
  return (
    <OutcomeSummary
      outcome={outcome}
      onEdit={() => {
        setIsEditing(true);
      }}
    />
  );
}
