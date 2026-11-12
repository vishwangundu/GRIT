import type { ReactElement, ReactNode } from 'react';

import { AppShell, type NavItem } from '@/components/shell/AppShell';
import { NotificationBell } from '@/components/shell/NotificationBell';

const NAV: readonly NavItem[] = [
  { href: '/student', label: 'Dashboard', icon: 'dashboard' },
  { href: '/student/book', label: 'Book', icon: 'book' },
  { href: '/student/leaderboard', label: 'Leaderboard', icon: 'leaderboard' },
];

export default function StudentLayout({
  children,
}: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <AppShell area="student" nav={NAV} headerActions={<NotificationBell />}>
      {children}
    </AppShell>
  );
}
