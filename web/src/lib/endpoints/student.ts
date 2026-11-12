import { newIdempotencyKey, request } from '@/lib/api';
import type { BookingResponse, StateResponse } from '@/types/models';

export function bookSlot(slotId: string): Promise<BookingResponse> {
  return request<BookingResponse>('POST', '/student/bookings', {
    body: { slot_id: slotId },
    idempotencyKey: newIdempotencyKey(),
  });
}

export function cancelBooking(): Promise<StateResponse> {
  return request<StateResponse>('DELETE', '/student/bookings/current');
}

export function markAllRead(): Promise<{ marked: number }> {
  return request<{ marked: number }>('POST', '/student/notifications/read');
}
