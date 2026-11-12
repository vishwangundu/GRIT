import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/supabase/client', () => ({ getAccessToken: vi.fn(() => Promise.resolve('jwt-1')) }));
vi.mock('@/lib/env', () => ({
  PUBLIC_ENV: { apiUrl: 'https://api.test/api/v1', supabaseUrl: '', supabaseAnonKey: '' },
  requireEnv: (value: string) => value,
}));

import { ApiError, OFFLINE_MESSAGE, getJson, isSignedOut, request } from './api';
import { cancelBooking, bookSlot, markAllRead } from './endpoints/student';
import {
  addWindow,
  cancelInterview,
  editOutcome,
  recordOutcome,
  removeWindow,
  setSlotBlocked,
} from './endpoints/interviewer';
import {
  decideFlag,
  raiseFlag,
  reassignBooking,
  remindInterviewer,
  sendNudges,
} from './endpoints/admin';
import { PATHS } from './endpoints/paths';

const fetchMock = vi.fn<typeof fetch>();
const NO_SHOW = { result: 'no_show', feedback_to_student: '', internal_notes: '' } as const;

function reply(status: number, body: unknown): void {
  fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(body), { status }));
}

function lastCall(): { url: string; init: RequestInit; headers: Headers } {
  const [url, init] = fetchMock.mock.calls.at(-1) ?? [];
  const safeInit = init ?? {};
  const href = typeof url === 'string' ? url : '';
  return { url: href, init: safeInit, headers: new Headers(safeInit.headers) };
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

describe('request', () => {
  it('sends the bearer token and parses JSON', async () => {
    reply(200, { role: 'student' });
    await expect(getJson(PATHS.me)).resolves.toEqual({ role: 'student' });
    expect(lastCall().url).toBe('https://api.test/api/v1/me');
    expect(lastCall().headers.get('Authorization')).toBe('Bearer jwt-1');
  });

  it('turns the API error shape into ApiError', async () => {
    reply(409, {
      error: { code: 'slot_taken', message: 'That slot was just taken. Pick another one.' },
    });
    const error = await request('POST', '/student/bookings').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: 'slot_taken', status: 409 });
  });

  it('shows the offline message when the API cannot be reached', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('network'));
    await expect(getJson('/me')).rejects.toMatchObject({
      code: 'offline',
      message: OFFLINE_MESSAGE,
    });
  });

  it('never fakes state on an unexpected error body', async () => {
    reply(500, 'oops');
    await expect(getJson('/me')).rejects.toMatchObject({ code: 'server_error', status: 500 });
  });

  it('recognises an expired session', () => {
    expect(isSignedOut(new ApiError('unauthorized', 'x', 401))).toBe(true);
    expect(isSignedOut(new ApiError('forbidden', 'x', 403))).toBe(false);
    expect(isSignedOut(undefined)).toBe(false);
  });
});

describe('endpoints', () => {
  it('books with an idempotency key', async () => {
    reply(201, {});
    await bookSlot('s1');
    expect(lastCall().headers.get('Idempotency-Key')).toBeTruthy();
    expect(lastCall().init.body).toBe(JSON.stringify({ slot_id: 's1' }));
  });

  it.each([
    ['cancel booking', () => cancelBooking(), 'DELETE', '/student/bookings/current'],
    ['mark read', () => markAllRead(), 'POST', '/student/notifications/read'],
    ['record', () => recordOutcome('b1', NO_SHOW), 'POST', '/interviewer/interviews/b1/outcome'],
    ['edit', () => editOutcome('b1', NO_SHOW), 'PUT', '/interviewer/interviews/b1/outcome'],
    [
      'cancel interview',
      () => cancelInterview('s1', 'illness'),
      'POST',
      '/interviewer/slots/s1/cancel',
    ],
    [
      'add window',
      () => addWindow({ date: '2026-11-20', start: '18:00', end: '19:00' }),
      'POST',
      '/interviewer/availability',
    ],
    ['remove window', () => removeWindow('w1'), 'DELETE', '/interviewer/availability/w1'],
    ['block', () => setSlotBlocked('s1', true), 'PATCH', '/interviewer/slots/s1'],
    ['nudge', () => sendNudges({ min_days_waiting: 7 }), 'POST', '/admin/nudges'],
    ['remind', () => remindInterviewer('b1'), 'POST', '/admin/reminders/b1'],
    ['reassign', () => reassignBooking('b1', 'i2'), 'POST', '/admin/bookings/b1/reassign'],
    [
      'flag',
      () => raiseFlag({ student_id: 'u', badge_id: 1, source: 'tip' }),
      'POST',
      '/admin/flags',
    ],
    [
      'decide',
      () => decideFlag('f1', { decision: 'dismiss', note: 'ok' }),
      'POST',
      '/admin/flags/f1/decision',
    ],
  ])('%s calls the right route', async (_name, call, method, path) => {
    reply(200, {});
    await call();
    expect(lastCall().init.method).toBe(method);
    expect(lastCall().url).toBe(`https://api.test/api/v1${path}`);
  });

  it('builds tracker and schedule paths', () => {
    expect(PATHS.tracker('booked', null)).toBe('/admin/tracker?tab=booked');
    expect(PATHS.tracker('results', 2)).toBe('/admin/tracker?tab=results&badge_id=2');
    expect(PATHS.schedule('2026-11-19')).toBe('/interviewer/schedule?date=2026-11-19');
  });
});
