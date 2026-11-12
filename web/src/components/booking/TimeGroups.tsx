import type { ReactElement } from 'react';

import { formatTime } from '@/lib/time';
import type { SlotTime } from '@/types/models';

const PERIODS = [
  { key: 'morning', label: 'Morning' },
  { key: 'afternoon', label: 'Afternoon' },
  { key: 'evening', label: 'Evening' },
] as const;

interface Props {
  times: SlotTime[];
  selected: string | null;
  onSelect: (slot: SlotTime) => void;
}

export function TimeGroups({ times, selected, onSelect }: Readonly<Props>): ReactElement {
  return (
    <div className="flex flex-col gap-5">
      {PERIODS.map((period) => {
        const group = times.filter((t) => t.period === period.key);
        if (group.length === 0) return null;
        return (
          <fieldset key={period.key}>
            <legend className="mb-2 flex items-baseline gap-2 text-sm font-semibold">
              {period.label}
              <span className="text-xs font-normal text-muted">{group.length}</span>
            </legend>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-6">
              {group.map((slot) => (
                <button
                  key={slot.slot_id}
                  type="button"
                  aria-pressed={selected === slot.slot_id}
                  onClick={() => {
                    onSelect(slot);
                  }}
                  className="h-9 rounded-lg border border-line-strong bg-white text-sm font-medium transition hover:border-grit-blue-strong hover:text-grit-blue-strong aria-pressed:border-grit-blue-strong aria-pressed:bg-grit-blue-strong aria-pressed:text-white"
                >
                  {formatTime(slot.start_at)}
                </button>
              ))}
            </div>
          </fieldset>
        );
      })}
    </div>
  );
}
