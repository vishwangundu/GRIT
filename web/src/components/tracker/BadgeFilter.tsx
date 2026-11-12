import type { ReactElement } from 'react';

import { INPUT_CLASS } from '@/components/ui/Field';
import type { Tracker } from '@/types/models';

interface Props {
  badges: Tracker['badges'];
  value: number | null;
  onChange: (badgeId: number | null) => void;
}

export function BadgeFilter({ badges, value, onChange }: Readonly<Props>): ReactElement {
  return (
    <label className="flex flex-col gap-1 text-sm font-semibold">
      Badge
      <select
        value={value ?? ''}
        onChange={(e) => {
          onChange(e.target.value ? Number(e.target.value) : null);
        }}
        className={INPUT_CLASS}
      >
        <option value="">All badges</option>
        {badges.map((b) => (
          <option key={b.id} value={b.id}>
            {b.track} · {b.name}
          </option>
        ))}
      </select>
    </label>
  );
}
