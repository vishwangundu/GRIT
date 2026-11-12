'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { Empty, InlineError, Loading } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { useApi } from '@/hooks/use-api';
import { reassignBooking } from '@/lib/endpoints/admin';
import { PATHS } from '@/lib/endpoints/paths';
import type { BookedRow, ReassignOptions } from '@/types/models';

interface Props {
  row: BookedRow | null;
  onClose: () => void;
  onDone: () => Promise<unknown>;
}

export function ReassignDialog({ row, onClose, onDone }: Readonly<Props>): ReactElement {
  const { data } = useApi<ReassignOptions>(row ? PATHS.reassignOptions(row.booking_id) : null);
  const [choice, setChoice] = useState<string | null>(null);
  const action = useAction();

  function confirm(): void {
    if (!row || !choice) return;
    void action.run(async () => {
      await reassignBooking(row.booking_id, choice);
      await onDone();
      onClose();
      return undefined;
    });
  }

  return (
    <Dialog isOpen={row !== null} title={`Reassign ${row?.name ?? ''}`} onClose={onClose}>
      {!data ? <Loading /> : null}
      {data?.options.length === 0 ? (
        <Empty>No cleared interviewer is free at that time.</Empty>
      ) : null}
      <fieldset className="flex flex-col gap-2 text-sm">
        <legend className="sr-only">Interviewer</legend>
        {data?.options.map((option) => (
          <label key={option.interviewer_id} className="flex items-center gap-2">
            <input
              type="radio"
              name="reassign"
              checked={choice === option.interviewer_id}
              onChange={() => {
                setChoice(option.interviewer_id);
              }}
              className="size-4"
            />
            {option.name}
          </label>
        ))}
      </fieldset>
      <InlineError message={action.error} />
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
        <Button disabled={!choice} isBusy={action.isBusy} onClick={confirm}>
          Reassign
        </Button>
      </div>
    </Dialog>
  );
}
