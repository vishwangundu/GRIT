import type { ReactElement, ReactNode } from 'react';

import { AppShell, type NavItem } from '@/components/shell/AppShell';

const NAV: readonly NavItem[] = [
  { href: '/interviewer', label: 'Schedule', icon: 'schedule' },
  { href: '/interviewer/availability', label: 'Availability', icon: 'availability' },
];

export default function InterviewerLayout({
  children,
}: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <AppShell area="interviewer" nav={NAV}>
      {children}
    </AppShell>
  );
}
