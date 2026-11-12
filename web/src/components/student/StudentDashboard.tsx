'use client';

import type { ReactElement } from 'react';

import { Empty, ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useNow } from '@/hooks/use-now';
import { useRules } from '@/hooks/use-session';
import { PATHS } from '@/lib/endpoints/paths';
import type { Dashboard } from '@/types/models';

import { InterviewCard } from './InterviewCard';
import { JourneyHistory } from './JourneyHistory';
import { StatsRow } from './StatsRow';
import { TrackProgress } from './TrackProgress';

const MS_PER_SECOND = 1000;

export function StudentDashboard(): ReactElement {
  const { data: rules } = useRules();
  const refresh = rules ? rules.dashboard_poll_seconds * MS_PER_SECOND : 0;
  const { data, error, mutate } = useApi<Dashboard>(PATHS.dashboard, refresh);
  const now = useNow();

  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data || !rules) return <Loading label="Loading your dashboard…" />;
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-3xl text-ink">Hi {data.name.split(' ')[0]}</h1>
        <p className="mt-1 text-sm text-ink-soft">{data.campus} campus</p>
      </div>
      <StatsRow stats={data.stats} />
      {data.journey ? (
        <InterviewCard
          dashboard={data}
          journey={data.journey}
          passMiles={rules.pass_miles}
          now={now}
        />
      ) : (
        <Empty>No badge journey yet. Keep clearing skills to unlock your first interview.</Empty>
      )}
      <div className="grid items-start gap-4 lg:grid-cols-2">
        <TrackProgress ladder={data.ladder} />
        <JourneyHistory events={data.events} />
      </div>
    </div>
  );
}
