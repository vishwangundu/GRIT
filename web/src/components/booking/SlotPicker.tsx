'use client';

import { type ReactElement, useState } from 'react';

import { Card } from '@/components/ui/Card';
import { plural } from '@/lib/labels';
import { formatDate } from '@/lib/time';
import type { SlotDay, SlotTime } from '@/types/models';

import { DayStrip } from './DayStrip';
import { TimeGroups } from './TimeGroups';

interface Props {
  days: SlotDay[];
  selectedSlot: string | null;
  onPick: (slot: SlotTime) => void;
}

/** Noon IST on a "YYYY-MM-DD" day, so the date label can't drift across midnight. */
const middayOf = (dateKey: string): string => `${dateKey}T06:30:00Z`;

export function SlotPicker({ days, selectedSlot, onPick }: Readonly<Props>): ReactElement {
  const firstOpen = days.find((d) => d.open_count > 0)?.date ?? null;
  const [picked, setPicked] = useState<string | null>(null);
  const day = days.find((d) => d.date === (picked ?? firstOpen));
  return (
    <Card>
      <DayStrip days={days} selected={day?.date ?? null} onSelect={setPicked} />
      {day ? (
        <div className="mt-5 border-t border-line pt-4">
          <p className="mb-4 text-sm">
            <span className="font-semibold">{formatDate(middayOf(day.date))}</span>
            <span className="text-muted">
              {' '}
              · {plural(day.open_count, 'open slot')} · times in IST
            </span>
          </p>
          <TimeGroups times={day.times} selected={selectedSlot} onSelect={onPick} />
        </div>
      ) : null}
    </Card>
  );
}
