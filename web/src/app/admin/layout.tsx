import type { ReactElement, ReactNode } from 'react';

import { AppShell, type NavItem } from '@/components/shell/AppShell';

const NAV: readonly NavItem[] = [{ href: '/admin', label: 'Tracker' }];

export default function AdminLayout({ children }: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <AppShell area="admin" nav={NAV}>
      {children}
    </AppShell>
  );
}
