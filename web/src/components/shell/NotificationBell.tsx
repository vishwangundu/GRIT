'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactElement } from 'react';

import { UnreadBadge } from './UnreadBadge';

const MESSAGES_PATH = '/student/messages';

/** Header bell that opens Messages, with the red unread count on its corner. */
export function NotificationBell(): ReactElement {
  const isCurrent = usePathname() === MESSAGES_PATH;
  return (
    <Link
      href={MESSAGES_PATH}
      aria-label="Messages"
      title="Messages"
      aria-current={isCurrent ? 'page' : undefined}
      className="relative flex h-9 w-9 items-center justify-center rounded-full text-white/80 transition hover:bg-white/15 hover:text-white aria-[current=page]:bg-white/15 aria-[current=page]:text-white"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      <UnreadBadge className="absolute -top-0.5 -right-0.5 min-w-[1.125rem] text-center leading-[1.125rem] ring-2 ring-ink" />
    </Link>
  );
}
