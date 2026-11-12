'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useSWRConfig } from 'swr';

import { ApiError } from '@/lib/api';
import { PATHS } from '@/lib/endpoints/paths';
import { bookSlot } from '@/lib/endpoints/student';
import type { SlotTime } from '@/types/models';

interface BookingState {
  pending: SlotTime | null;
  isBusy: boolean;
  error: string | null;
  choose: (slot: SlotTime | null) => void;
  confirm: () => Promise<void>;
}

/** Confirm flow: on slot_taken, show the server message and refresh the picker. */
export function useBooking(): BookingState {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const [pending, setPending] = useState<SlotTime | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm(): Promise<void> {
    if (!pending) return;
    setIsBusy(true);
    setError(null);
    try {
      await bookSlot(pending.slot_id);
      await Promise.all([mutate(PATHS.dashboard), mutate(PATHS.notifications)]);
      router.push('/student');
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'Booking failed. Try again.');
      if (err instanceof ApiError && err.code === 'slot_taken') await mutate(PATHS.slots);
    } finally {
      setIsBusy(false);
    }
  }

  function choose(slot: SlotTime | null): void {
    setError(null);
    setPending(slot);
  }

  return { pending, isBusy, error, choose, confirm };
}
