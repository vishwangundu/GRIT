import { newIdempotencyKey, request } from '@/lib/api';
import type {
  OutcomeCreate,
  OutcomeEdit,
  OutcomeResponse,
  SlotPatched,
  WindowCreate,
  WindowCreated,
} from '@/types/models';

export function recordOutcome(bookingId: string, body: OutcomeCreate): Promise<OutcomeResponse> {
  return request<OutcomeResponse>('POST', `/interviewer/interviews/${bookingId}/outcome`, {
    body,
    idempotencyKey: newIdempotencyKey(),
  });
}

export function editOutcome(bookingId: string, body: OutcomeEdit): Promise<OutcomeResponse> {
  return request<OutcomeResponse>('PUT', `/interviewer/interviews/${bookingId}/outcome`, { body });
}

export function cancelInterview(slotId: string, reason: string): Promise<unknown> {
  return request('POST', `/interviewer/slots/${slotId}/cancel`, { body: { reason } });
}

export function addWindow(body: WindowCreate): Promise<WindowCreated> {
  return request<WindowCreated>('POST', '/interviewer/availability', { body });
}

export function removeWindow(windowId: string): Promise<unknown> {
  return request('DELETE', `/interviewer/availability/${windowId}`);
}

export function setSlotBlocked(slotId: string, blocked: boolean): Promise<SlotPatched> {
  return request<SlotPatched>('PATCH', `/interviewer/slots/${slotId}`, { body: { blocked } });
}
