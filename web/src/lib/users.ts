import type { UserRole, UserRow } from '@/types/models';

export type RoleFilter = UserRole | 'all';

/** Users matching a role and a free-text search over name and email (case-insensitive). */
export function filterUsers(users: readonly UserRow[], role: RoleFilter, query: string): UserRow[] {
  const needle = query.trim().toLowerCase();
  return users.filter(
    (u) =>
      (role === 'all' || u.role === role) &&
      (needle === '' ||
        u.name.toLowerCase().includes(needle) ||
        u.email.toLowerCase().includes(needle)),
  );
}
