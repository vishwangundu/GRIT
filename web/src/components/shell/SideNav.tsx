'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactElement } from 'react';

import {
  CalendarIcon,
  CalendarPlusIcon,
  ChartIcon,
  ClockIcon,
  HomeIcon,
  TrophyIcon,
  UsersIcon,
} from '@/components/ui/icons';

import type { NavItem } from './PageNav';
import { SignOutIcon } from './SignOutIcon';

const ICONS: Record<NavItem['icon'], () => ReactElement> = {
  dashboard: HomeIcon,
  book: CalendarPlusIcon,
  leaderboard: TrophyIcon,
  schedule: CalendarIcon,
  availability: ClockIcon,
  tracker: ChartIcon,
  users: UsersIcon,
};

/** Left-hand section nav (large screens only): a white panel that stays beside the
 * content while it scrolls. */
export function SideNav({
  title,
  items,
  onSignOut,
}: Readonly<{ title: string; items: readonly NavItem[]; onSignOut: () => void }>): ReactElement {
  const pathname = usePathname();
  return (
    <nav aria-label="Sections" className="flex h-full flex-col gap-1 grit-panel p-3">
      <p className="px-3 pt-1 pb-2 text-xs font-semibold tracking-wide text-muted uppercase">
        {title}
      </p>
      {items.map((item) => {
        const Icon = ICONS[item.icon];
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={pathname === item.href ? 'page' : undefined}
            className="flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-semibold text-ink-soft transition hover:bg-sand hover:text-ink aria-[current=page]:bg-grit-blue-strong aria-[current=page]:text-white aria-[current=page]:shadow-sm"
          >
            <Icon />
            {item.label}
          </Link>
        );
      })}
      <button
        type="button"
        onClick={onSignOut}
        className="mt-auto flex min-h-10 items-center gap-3 rounded-xl border-t border-line px-3 pt-1 text-sm font-semibold text-grit-red-strong transition hover:bg-[#fdecec]"
      >
        <SignOutIcon />
        Sign out
      </button>
    </nav>
  );
}
