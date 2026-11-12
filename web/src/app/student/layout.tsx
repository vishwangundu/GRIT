import type { ReactElement, ReactNode } from 'react';

import { AppShell, type NavItem } from '@/components/shell/AppShell';
import { NotificationBell } from '@/components/shell/NotificationBell';

const NAV: readonly NavItem[] = [
  { href: '/student', label: 'Dashboard' },
  { href: '/student/book', label: 'Book' },
  { href: '/student/leaderboard', label: 'Leaderboard' },
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
