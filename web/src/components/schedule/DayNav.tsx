import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { addDays, dayLabel, istDateKey } from '@/lib/time';

interface Props {
  date: string;
  onChange: (date: string) => void;
}

export function DayNav({ date, onChange }: Readonly<Props>): ReactElement {
  const label = dayLabel(date);
  const today = istDateKey();
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="secondary"
        onClick={() => {
          onChange(addDays(date, -1));
        }}
      >
        ← Previous
      </Button>
      <Button
        variant="secondary"
        disabled={date === today}
        onClick={() => {
          onChange(today);
        }}
      >
        Today
      </Button>
      <Button
        variant="secondary"
        onClick={() => {
          onChange(addDays(date, 1));
        }}
      >
        Next →
      </Button>
      <h1 className="ml-1 text-2xl" aria-live="polite">
        {label.weekday}, {label.day} {label.month}
        {date === today ? ' · Today' : ''}
      </h1>
    </div>
  );
}
