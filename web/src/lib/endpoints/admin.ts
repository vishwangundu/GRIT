import { request } from '@/lib/api';
import type {
  FlagCreate,
  FlagCreated,
  FlagDecided,
  FlagDecision,
  NudgeRequest,
  NudgeResponse,
  ReassignResponse,
  SentResponse,
} from '@/types/models';

export function sendNudges(body: NudgeRequest): Promise<NudgeResponse> {
  return request<NudgeResponse>('POST', '/admin/nudges', { body });
}

export function remindInterviewer(bookingId: string): Promise<SentResponse> {
  return request<SentResponse>('POST', `/admin/reminders/${bookingId}`);
}

export function reassignBooking(
  bookingId: string,
  interviewerId: string,
): Promise<ReassignResponse> {
  return request<ReassignResponse>('POST', `/admin/bookings/${bookingId}/reassign`, {
    body: { interviewer_id: interviewerId },
  });
}

export function raiseFlag(body: FlagCreate): Promise<FlagCreated> {
  return request<FlagCreated>('POST', '/admin/flags', { body });
}

export function decideFlag(flagId: string, body: FlagDecision): Promise<FlagDecided> {
  return request<FlagDecided>('POST', `/admin/flags/${flagId}/decision`, { body });
}
