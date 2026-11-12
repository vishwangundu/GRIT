import type { ReactElement } from 'react';

import type { Tracker, TrackerTab } from '@/types/models';

interface Props {
  tiles: Tracker['tiles'];
  active: TrackerTab;
  onSelect: (tab: TrackerTab) => void;
}

export function TrackerTiles({ tiles, active, onSelect }: Readonly<Props>): ReactElement {
  const items: { tab: TrackerTab; label: string; value: number; note?: string }[] = [
    { tab: 'notbooked', label: 'Not booked', value: tiles.not_booked },
    { tab: 'booked', label: 'Booked', value: tiles.booked },
    {
      tab: 'awaiting',
      label: 'Awaiting result',
      value: tiles.awaiting,
      note: tiles.awaiting_overdue > 0 ? `${String(tiles.awaiting_overdue)} overdue` : undefined,
    },
    { tab: 'results', label: 'Results recorded', value: tiles.results },
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {items.map((item) => (
        <button
          key={item.tab}
          type="button"
          aria-pressed={active === item.tab}
          onClick={() => {
            onSelect(item.tab);
          }}
          className="grit-panel p-3 text-left hover:border-line-strong aria-pressed:border-grit-blue-strong aria-pressed:ring-1 aria-pressed:ring-grit-blue-strong"
        >
          <span className="block text-xs font-semibold text-muted uppercase">{item.label}</span>
          <span className="block text-2xl font-bold">{item.value}</span>
          {item.note ? (
            <span className="text-xs font-semibold text-grit-red-strong">{item.note}</span>
          ) : null}
        </button>
      ))}
    </div>
  );
}
