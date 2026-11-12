import type { ReactElement, ReactNode } from 'react';

import { AppShell, type NavItem } from '@/components/shell/AppShell';

const NAV: readonly NavItem[] = [
  { href: '/student', label: 'Dashboard' },
  { href: '/student/book', label: 'Book' },
  { href: '/student/messages', label: 'Messages', showUnread: true },
  { href: '/student/leaderboard', label: 'Leaderboard' },
];

export default function StudentLayout({
  children,
}: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <AppShell area="student" nav={NAV}>
      {children}
    </AppShell>
  );
}
