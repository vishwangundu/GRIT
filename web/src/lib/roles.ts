import { z } from 'zod';

import type { Role } from '@/types/models';

export const HOME_FOR_ROLE: Record<Role, string> = {
  student: '/student',
  interviewer: '/interviewer',
  admin: '/admin',
};

/** Only allow redirects back into our own role areas (blocks open redirects). */
const nextPathSchema = z.string().regex(/^\/(student|interviewer|admin)(\/[\w\-/?=&]*)?$/u);

export function safeNextPath(raw: string | null, role: Role): string {
  const parsed = nextPathSchema.safeParse(raw);
  const home = HOME_FOR_ROLE[role];
  return parsed.success && parsed.data.startsWith(home) ? parsed.data : home;
}
