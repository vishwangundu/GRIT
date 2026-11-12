'use client';

import { type ReactElement, useState } from 'react';

import { CancelInterviewDialog } from '@/components/schedule/CancelInterviewDialog';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Empty, ErrorBox, InlineError, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useRules } from '@/hooks/use-session';
import { ApiError } from '@/lib/api';
import { removeWindow, setSlotBlocked } from '@/lib/endpoints/interviewer';
import { PATHS } from '@/lib/endpoints/paths';
import { formatDate, formatRange } from '@/lib/time';
import type { Availability, AvailabilitySlot } from '@/types/models';

import { AddWindowForm } from './AddWindowForm';
import { SlotChip } from './SlotChip';

export function AvailabilityManager(): ReactElement {
  const { data, error, mutate } = useApi<Availability>(PATHS.availability);
  const { data: rules } = useRules();
  const [actionError, setActionError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<AvailabilitySlot | null>(null);

  async function run(action: () => Promise<unknown>): Promise<void> {
    setActionError(null);
    try {
      await action();
      await mutate();
    } catch (err: unknown) {
      setActionError(err instanceof ApiError ? err.message : 'That change failed.');
    }
  }

  function onTap(slot: AvailabilitySlot): void {
    if (slot.status === 'booked') setCancelling(slot);
    else void run(() => setSlotBlocked(slot.slot_id, slot.status === 'open'));
  }

  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data || !rules) return <Loading label="Loading availability…" />;
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-3xl">Availability · next {rules.book_horizon_days} days</h1>
      <AddWindowForm rules={rules} onAdded={() => mutate()} />
      <InlineError message={actionError} />
      {data.windows.length === 0 ? <Empty>No windows yet. Add one above.</Empty> : null}
      {data.windows.map((window) => (
        <Card key={window.window_id}>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">
              {formatDate(window.starts_at)} · {formatRange(window.starts_at, window.ends_at)}
            </h2>
            <Button
              variant="ghost"
              disabled={!window.can_remove}
              title={window.can_remove ? undefined : 'Cancel its bookings first'}
              onClick={() => void run(() => removeWindow(window.window_id))}
            >
              Remove window
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {window.slots.map((slot) => (
              <SlotChip key={slot.slot_id} slot={slot} onTap={onTap} />
            ))}
          </div>
        </Card>
      ))}
      <CancelInterviewDialog
        slotId={cancelling?.slot_id ?? null}
        studentName={cancelling?.student_first_name ?? 'this student'}
        onClose={() => {
          setCancelling(null);
        }}
        onDone={() => mutate()}
      />
    </div>
  );
}
