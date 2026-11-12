'use client';

import { type ReactElement, useState } from 'react';

import { ResultForm } from '@/components/schedule/ResultForm';
import { Dialog } from '@/components/ui/Dialog';
import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useRules } from '@/hooks/use-session';
import { PATHS } from '@/lib/endpoints/paths';
import type { InterviewDetail, ResultRow } from '@/types/models';

interface Props {
  row: ResultRow | null;
  onClose: () => void;
  onDone: () => Promise<unknown>;
}

/** FR-A6: admins can change any result after the 2 h window, with an audit note. */
export function OverrideDialog({ row, onClose, onDone }: Readonly<Props>): ReactElement {
  const { data, error } = useApi<InterviewDetail>(row ? PATHS.interview(row.booking_id) : null);
  const { data: rules } = useRules();
  const [note, setNote] = useState('');

  async function saved(): Promise<void> {
    await onDone();
    onClose();
  }

  return (
    <Dialog
      isOpen={row !== null}
      title={`Override result: ${row?.name ?? ''}`}
      onClose={onClose}
      size="lg"
    >
      {error ? <ErrorBox error={error} /> : null}
      {!data || !rules ? <Loading /> : null}
      {data?.outcome && rules ? (
        <div className="flex flex-col gap-4">
          <Field id="edit-note" label="Audit note (required)" hint="Why the result is changing.">
            <textarea
              id="edit-note"
              rows={2}
              value={note}
              onChange={(e) => {
                setNote(e.target.value);
              }}
              className={INPUT_CLASS}
            />
          </Field>
          <ResultForm
            bookingId={data.booking_id}
            rules={rules}
            existing={data.outcome}
            editNote={note}
            onSaved={saved}
            onCancel={onClose}
            stickyActions
          />
        </div>
      ) : null}
    </Dialog>
  );
}
