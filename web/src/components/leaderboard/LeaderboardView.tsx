'use client';

import { type ReactElement, useState } from 'react';

import { ChipTabs } from '@/components/ui/ChipTabs';
import { Empty, ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { PATHS } from '@/lib/endpoints/paths';
import type { Leaderboard } from '@/types/models';

import { LeaderboardTable } from './LeaderboardTable';

type Tier = 'qual' | 'pre';
const TABS = [
  { key: 'qual', label: 'Qualiflyers' },
  { key: 'pre', label: 'Pre-Qualiflyers' },
] as const;

function Body({ tier }: Readonly<{ tier: Tier }>): ReactElement {
  const { data, error, mutate } = useApi<Leaderboard>(PATHS.leaderboard(tier));
  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data) return <Loading />;
  if (data.rows.length === 0) return <Empty>Nobody here yet.</Empty>;
  return <LeaderboardTable rows={data.rows} />;
}

/** Opens on the student's own tier; the first request tells us which one that is. */
export function LeaderboardView(): ReactElement {
  const [picked, setPicked] = useState<Tier | null>(null);
  const { data: probe } = useApi<Leaderboard>(picked ? null : PATHS.leaderboard('pre'));
  const tier: Tier = picked ?? probe?.my_tier ?? 'pre';
  return (
    <div className="grit-fill flex flex-col gap-3">
      <h1 className="text-3xl">Leaderboard</h1>
      <ChipTabs options={TABS} value={tier} onChange={setPicked} label="Leaderboard tier" />
      <Body tier={tier} />
    </div>
  );
}
