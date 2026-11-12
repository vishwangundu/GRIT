'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { InlineError } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { cancelInterview } from '@/lib/endpoints/interviewer';

import { CANCEL_REASONS, ReasonPicker } from './ReasonPicker';

interface Props {
  slotId: string | null;
  studentName: string;
  onClose: () => void;
  onDone: () => Promise<unknown>;
}

export function CancelInterviewDialog(props: Readonly<Props>): ReactElement {
  const { slotId, studentName, onClose, onDone } = props;
  const [reason, setReason] = useState<string>(CANCEL_REASONS[0]);
  const action = useAction();

  function confirm(): void {
    if (!slotId) return;
    void action.run(async () => {
      await cancelInterview(slotId, reason);
      await onDone();
      onClose();
      return undefined;
    });
  }

  return (
    <Dialog
      isOpen={slotId !== null}
      title={`Cancel interview with ${studentName}?`}
      onClose={onClose}
    >
      <ReasonPicker value={reason} onChange={setReason} />
      <p className="mt-3 text-sm text-ink-soft">
        The student keeps their attempt and gets first pick of new slots.
      </p>
      <InlineError message={action.error} />
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Keep
        </Button>
        <Button variant="danger" isBusy={action.isBusy} onClick={confirm}>
          Cancel interview
        </Button>
      </div>
    </Dialog>
  );
}
