'use client';

import type { ReactElement } from 'react';

import { useApi } from '@/hooks/use-api';
import { useRules } from '@/hooks/use-session';
import { PATHS } from '@/lib/endpoints/paths';
import type { Inbox } from '@/types/models';

const MS_PER_SECOND = 1000;

export function UnreadBadge(): ReactElement | null {
  const { data: rules } = useRules();
  const refresh = rules ? rules.dashboard_poll_seconds * MS_PER_SECOND : 0;
  const { data } = useApi<Inbox>(PATHS.notifications, refresh);
  if (!data || data.unread_count === 0) return null;
  return (
    <span className="rounded-full bg-grit-red-strong px-1.5 text-xs font-bold text-white">
      {data.unread_count}
      <span className="sr-only"> unread</span>
    </span>
  );
}
