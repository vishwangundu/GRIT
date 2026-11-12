'use client';

import { type ReactElement, useState } from 'react';
import { useSWRConfig } from 'swr';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { InlineError } from '@/components/ui/StateView';
import { ApiError } from '@/lib/api';
import { PATHS } from '@/lib/endpoints/paths';
import { cancelBooking } from '@/lib/endpoints/student';

export function CancelBookingButton({ canCancel }: Readonly<{ canCancel: boolean }>): ReactElement {
  const { mutate } = useSWRConfig();
  const [isOpen, setIsOpen] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm(): Promise<void> {
    setIsBusy(true);
    setError(null);
    try {
      await cancelBooking();
      setIsOpen(false);
      await mutate(PATHS.dashboard);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'Could not cancel. Try again.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <>
      <Button
        variant="secondary"
        disabled={!canCancel}
        onClick={() => {
          setIsOpen(true);
        }}
      >
        Cancel
      </Button>
      <Dialog
        isOpen={isOpen}
        title="Cancel this interview?"
        onClose={() => {
          setIsOpen(false);
        }}
      >
        <p className="text-sm text-ink-soft">
          You can book again any time. Cancelling doesn’t use an attempt.
        </p>
        <InlineError message={error} />
        <div className="mt-4 flex justify-end gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              setIsOpen(false);
            }}
          >
            Keep it
          </Button>
          <Button variant="danger" isBusy={isBusy} onClick={() => void confirm()}>
            Cancel interview
          </Button>
        </div>
      </Dialog>
    </>
  );
}
