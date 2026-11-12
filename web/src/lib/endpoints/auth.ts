import { request } from '@/lib/api';
import type { Me, RegisterRequest } from '@/types/models';

/** Creates the student profile for the signed-in Supabase user. Role is decided by FastAPI. */
export function registerProfile(body: RegisterRequest): Promise<Me> {
  return request<Me>('POST', '/register', { body });
}
