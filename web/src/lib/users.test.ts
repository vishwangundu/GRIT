import { describe, expect, it } from 'vitest';

import type { UserRow } from '@/types/models';

import { filterUsers } from './users';

function user(name: string, email: string, role: UserRow['role']): UserRow {
  return {
    id: name,
    role,
    name,
    email,
    joined_at: '2026-11-12T00:00:00Z',
    campus: null,
    batch: null,
    miles: null,
    badge_count: 0,
  };
}

const USERS = [
  user('Priya Sharma', 'priya@demo.grit', 'interviewer'),
  user('Aarav Reddy', 'aarav@demo.grit', 'student'),
  user('Interview Team', 'admin@demo.grit', 'admin'),
];

describe('filterUsers', () => {
  it('keeps everyone for all roles and an empty search', () => {
    expect(filterUsers(USERS, 'all', '  ')).toHaveLength(3);
  });

  it('filters by role', () => {
    expect(filterUsers(USERS, 'student', '').map((u) => u.name)).toEqual(['Aarav Reddy']);
  });

  it('searches name and email, ignoring case', () => {
    expect(filterUsers(USERS, 'all', 'PRIYA').map((u) => u.name)).toEqual(['Priya Sharma']);
    expect(filterUsers(USERS, 'all', 'admin@').map((u) => u.role)).toEqual(['admin']);
  });

  it('combines role and search', () => {
    expect(filterUsers(USERS, 'admin', 'aarav')).toEqual([]);
  });
});
