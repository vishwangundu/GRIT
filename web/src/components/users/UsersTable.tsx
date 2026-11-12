import type { ReactElement } from 'react';

import { CELL, Table } from '@/components/tracker/Table';
import { PersonName } from '@/components/ui/Avatar';
import { Chip } from '@/components/ui/Chip';
import type { Tone } from '@/lib/tones';
import { formatDate } from '@/lib/time';
import type { UserRole, UserRow } from '@/types/models';

const HEADERS = ['User', 'Email', 'Role', 'Campus · Batch', 'Miles · Badges', 'Joined'] as const;

export const ROLE_LABELS: Record<UserRole, { label: string; tone: Tone }> = {
  admin: { label: 'Admin', tone: 'review' },
  interviewer: { label: 'Interviewer', tone: 'info' },
  student: { label: 'Student', tone: 'neutral' },
};

function placeOf(user: UserRow): string {
  const parts = [user.campus, user.batch ? `Batch ${user.batch}` : null].filter(Boolean);
  return parts.length > 0 ? parts.join(' · ') : '–';
}

function progressOf(user: UserRow): string {
  if (user.role !== 'student') return '–';
  const badges = `${String(user.badge_count)} badge${user.badge_count === 1 ? '' : 's'}`;
  return `${(user.miles ?? 0).toLocaleString('en-IN')} · ${badges}`;
}

export function UsersTable({ users }: Readonly<{ users: UserRow[] }>): ReactElement {
  return (
    <Table headers={HEADERS} isEmpty={users.length === 0} emptyText="No users match.">
      {users.map((user) => {
        const role = ROLE_LABELS[user.role];
        return (
          <tr key={user.id}>
            <td className={CELL}>
              <PersonName name={user.name} />
            </td>
            <td className={CELL}>
              <a
                href={`mailto:${user.email}`}
                className="text-grit-blue-strong underline-offset-4 hover:underline"
              >
                {user.email}
              </a>
            </td>
            <td className={CELL}>
              <Chip tone={role.tone}>{role.label}</Chip>
            </td>
            <td className={CELL}>{placeOf(user)}</td>
            <td className={CELL}>{progressOf(user)}</td>
            <td className={`${CELL} whitespace-nowrap`}>{formatDate(user.joined_at)}</td>
          </tr>
        );
      })}
    </Table>
  );
}
