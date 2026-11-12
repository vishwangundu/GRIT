/**
 * The only place that calls FastAPI. Attaches the Supabase JWT and turns the API's
 * {"error": {"code", "message"}} shape into ApiError.
 */
import { PUBLIC_ENV, requireEnv } from '@/lib/env';
import { getAccessToken } from '@/lib/supabase/client';

const HTTP_UNAUTHORIZED = 401;

export const OFFLINE_MESSAGE = "Can't reach GRIT right now. Try again in a minute.";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface RequestOptions {
  body?: unknown;
  idempotencyKey?: string;
}

function isErrorBody(value: unknown): value is { error: { code: string; message: string } } {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false;
  const inner: unknown = value.error;
  return typeof inner === 'object' && inner !== null && 'code' in inner && 'message' in inner;
}

async function buildHeaders(options: RequestOptions): Promise<Headers> {
  const headers = new Headers({ Accept: 'application/json' });
  const token = await getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body !== undefined) headers.set('Content-Type', 'application/json');
  if (options.idempotencyKey) headers.set('Idempotency-Key', options.idempotencyKey);
  return headers;
}

async function send(method: Method, path: string, options: RequestOptions): Promise<Response> {
  const base = requireEnv(PUBLIC_ENV.apiUrl, 'NEXT_PUBLIC_API_URL');
  try {
    return await fetch(`${base}${path}`, {
      method,
      headers: await buildHeaders(options),
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: 'no-store',
    });
  } catch {
    throw new ApiError('offline', OFFLINE_MESSAGE, 0);
  }
}

export async function request<T>(
  method: Method,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await send(method, path, options);
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    if (isErrorBody(payload)) {
      throw new ApiError(payload.error.code, payload.error.message, response.status);
    }
    throw new ApiError('server_error', OFFLINE_MESSAGE, response.status);
  }
  return payload as T;
}

/** SWR fetcher: the key is the API path. */
export function getJson<T>(path: string): Promise<T> {
  return request<T>('GET', path);
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

/** True when the session is missing or expired (the user must sign in again). */
export function isSignedOut(error: ApiError | undefined): boolean {
  return error?.status === HTTP_UNAUTHORIZED;
}
