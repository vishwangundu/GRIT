'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { InlineError } from '@/components/ui/StateView';
import { formatDate, formatRange } from '@/lib/time';
import type { SlotTime } from '@/types/models';

interface Props {
  slot: SlotTime | null;
  isReschedule: boolean;
  isBusy: boolean;
  error: string | null;
  onConfirm: () => void;
  onClose: () => void;
}

export const COMMITMENT =
  'I’ll join from a laptop with my camera on, and I understand a missed interview counts as one attempt.';

export function ConfirmDialog(props: Readonly<Props>): ReactElement {
  const { slot, isReschedule, isBusy, error, onConfirm, onClose } = props;
  const [isAgreed, setIsAgreed] = useState(false);
  return (
    <Dialog
      isOpen={slot !== null}
      title={isReschedule ? 'Move your interview?' : 'Confirm your interview'}
      onClose={() => {
        setIsAgreed(false);
        onClose();
      }}
    >
      {slot ? (
        <p className="text-sm">
          <strong>{formatDate(slot.start_at)}</strong>, {formatRange(slot.start_at, slot.end_at)} ·
          Online (Google Meet). Your interviewer’s name appears once you’ve booked.
        </p>
      ) : null}
      <label className="mt-4 flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={isAgreed}
          onChange={(e) => {
            setIsAgreed(e.target.checked);
          }}
          className="mt-0.5 size-5"
        />
        <span>{COMMITMENT}</span>
      </label>
      <div className="mt-3">
        <InlineError message={error} />
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Back
        </Button>
        <Button disabled={!isAgreed} isBusy={isBusy} onClick={onConfirm}>
          {isReschedule ? 'Move interview' : 'Book interview'}
        </Button>
      </div>
    </Dialog>
  );
}
