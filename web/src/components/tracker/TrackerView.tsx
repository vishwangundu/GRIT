'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import type { ReactElement } from 'react';
import { z } from 'zod';

import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useRules } from '@/hooks/use-session';
import { PATHS } from '@/lib/endpoints/paths';
import type { Tracker, TrackerTab } from '@/types/models';

import { BadgeFilter } from './BadgeFilter';
import { TrackerBody } from './TrackerBody';

const tabSchema = z.enum(['notbooked', 'booked', 'awaiting', 'results']).catch('notbooked');
const badgeSchema = z.coerce.number().int().positive().nullable().catch(null);
const REFRESH_MS = 60_000;

export function TrackerView(): ReactElement {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const tab: TrackerTab = tabSchema.parse(params.get('tab'));
  const badgeId = badgeSchema.parse(params.get('badge'));
  const { data, error, mutate, isLoading } = useApi<Tracker>(
    PATHS.tracker(tab, badgeId),
    REFRESH_MS,
    true,
  );
  const { data: rules } = useRules();

  function go(nextTab: TrackerTab, nextBadge: number | null): void {
    const query = new URLSearchParams({ tab: nextTab });
    if (nextBadge !== null) query.set('badge', String(nextBadge));
    router.replace(`${pathname}?${query.toString()}`);
  }

  return (
    <div className="grit-fill flex flex-col gap-4">
      <h1 className="text-3xl">Interview tracker</h1>
      {data && data.badges.length > 0 ? (
        <BadgeFilter
          badges={data.badges}
          value={badgeId}
          onChange={(b) => {
            go(tab, b);
          }}
        />
      ) : null}
      {error ? <ErrorBox error={error} onRetry={() => void mutate()} /> : null}
      {!error && (!data || !rules) ? <Loading label="Loading tracker…" /> : null}
      {data && rules ? (
        <div
          aria-busy={isLoading}
          className={`grit-fill flex flex-col gap-4 transition-opacity ${isLoading ? 'pointer-events-none opacity-50' : ''}`}
        >
          <TrackerBody
            data={data}
            slowAfterDays={rules.slow_after_days}
            onTab={(t) => {
              go(t, badgeId);
            }}
            onChanged={() => mutate()}
          />
        </div>
      ) : null}
    </div>
  );
}
