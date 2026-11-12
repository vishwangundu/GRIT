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
  const { data, error, mutate } = useApi<Tracker>(PATHS.tracker(tab, badgeId), REFRESH_MS);
  const { data: rules } = useRules();

  function go(nextTab: TrackerTab, nextBadge: number | null): void {
    const query = new URLSearchParams({ tab: nextTab });
    if (nextBadge !== null) query.set('badge', String(nextBadge));
    router.replace(`${pathname}?${query.toString()}`);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-3xl">Interview tracker</h1>
        <BadgeFilter
          badges={data?.badges ?? []}
          value={badgeId}
          onChange={(b) => {
            go(tab, b);
          }}
        />
      </div>
      {error ? <ErrorBox error={error} onRetry={() => void mutate()} /> : null}
      {!error && (!data || !rules) ? <Loading label="Loading tracker…" /> : null}
      {data && rules ? (
        <TrackerBody
          data={data}
          slowAfterDays={rules.slow_after_days}
          onTab={(t) => {
            go(t, badgeId);
          }}
          onChanged={() => mutate()}
        />
      ) : null}
    </div>
  );
}
