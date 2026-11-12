'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactElement } from 'react';

export interface NavItem {
  href: string;
  label: string;
  /** Icon shown in the side nav. */
  icon: 'dashboard' | 'book' | 'leaderboard' | 'schedule' | 'availability' | 'tracker' | 'users';
}

/** Section tabs under the header. Hidden when a role has only one page. */
export function PageNav({ items }: Readonly<{ items: readonly NavItem[] }>): ReactElement | null {
  const pathname = usePathname();
  if (items.length < 2) return null;
  return (
    <nav
      aria-label="Sections"
      className="-mx-1 mb-5 flex overflow-x-auto overflow-y-hidden shadow-[inset_0_-1px_0_var(--color-line)] sm:mx-0 sm:gap-1"
    >
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          aria-current={pathname === item.href ? 'page' : undefined}
          className="inline-flex min-h-10 shrink-0 items-center gap-1.5 border-b-2 border-transparent px-1.5 text-[13px] sm:px-3 sm:text-sm font-semibold text-muted hover:text-ink aria-[current=page]:border-grit-blue-strong aria-[current=page]:text-grit-blue-strong"
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
