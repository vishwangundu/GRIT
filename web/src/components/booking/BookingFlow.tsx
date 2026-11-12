'use client';

import type { ReactElement } from 'react';

import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useBooking } from '@/hooks/use-booking';
import { PATHS } from '@/lib/endpoints/paths';
import type { SlotsResponse } from '@/types/models';

import { ConfirmDialog } from './ConfirmDialog';
import { NoSlots } from './NoSlots';
import { NotEligible } from './NotEligible';
import { RescheduleHeader } from './RescheduleHeader';
import { SlotPicker } from './SlotPicker';

function Picker({ data }: Readonly<{ data: SlotsResponse }>): ReactElement {
  const booking = useBooking();
  const current = data.current_booking;
  const hasSlots = data.days.some((d) => d.open_count > 0);
  const canPick = hasSlots && (current?.can_change ?? true);
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-3xl">{current ? 'Reschedule your interview' : 'Book your interview'}</h1>
      {current ? <RescheduleHeader current={current} /> : null}
      {hasSlots ? null : <NoSlots />}
      {canPick ? (
        <SlotPicker
          days={data.days}
          selectedSlot={booking.pending?.slot_id ?? null}
          onPick={booking.choose}
        />
      ) : null}
      <ConfirmDialog
        slot={booking.pending}
        isReschedule={current !== null}
        isBusy={booking.isBusy}
        error={booking.error}
        onConfirm={() => void booking.confirm()}
        onClose={() => {
          booking.choose(null);
        }}
      />
    </div>
  );
}

export function BookingFlow(): ReactElement {
  const { data, error, mutate } = useApi<SlotsResponse>(PATHS.slots);
  if (error?.code === 'not_eligible') return <NotEligible />;
  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data) return <Loading label="Finding open slots…" />;
  return <Picker data={data} />;
}
