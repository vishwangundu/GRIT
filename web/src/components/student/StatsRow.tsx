import type { ReactElement } from 'react';

import type { Stats } from '@/types/models';

function Stat({ label, value }: Readonly<{ label: string; value: string }>): ReactElement {
  return (
    <div className="grit-panel p-3">
      <dt className="text-xs font-semibold text-muted uppercase">{label}</dt>
      <dd className="mt-1 font-display text-lg leading-tight font-semibold sm:text-2xl">{value}</dd>
    </div>
  );
}

export function StatsRow({ stats }: Readonly<{ stats: Stats }>): ReactElement {
  const tier = stats.tier === 'qualiflyer' ? 'Qualiflyer' : 'Pre-Qualiflyer';
  const rank = stats.rank === null ? '' : ` #${String(stats.rank)}`;
  return (
    <dl className="grid grid-cols-3 gap-2 sm:gap-3">
      <Stat label="Miles" value={stats.miles.toLocaleString('en-IN')} />
      <Stat label="Tier" value={`${tier}${rank}`} />
      <Stat label="Badges" value={String(stats.badge_count)} />
    </dl>
  );
}
