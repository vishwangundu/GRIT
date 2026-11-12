'use client';

import { type ReactElement, useState } from 'react';

import { dayLabel } from '@/lib/time';
import type { SlotDay } from '@/types/models';

const WEEK = 7;

interface Props {
  days: SlotDay[];
  selected: string | null;
  onSelect: (date: string) => void;
}

function rangeLabel(week: SlotDay[]): string {
  const first = week[0];
  const last = week.at(-1);
  if (!first || !last) return '';
  const a = dayLabel(first.date);
  const b = dayLabel(last.date);
  return a.month === b.month
    ? `${a.day} – ${b.day} ${b.month}`
    : `${a.day} ${a.month} – ${b.day} ${b.month}`;
}

function DayCell(
  props: Readonly<{ day: SlotDay; isSelected: boolean; onSelect: (date: string) => void }>,
): ReactElement {
  const { day, isSelected } = props;
  const label = dayLabel(day.date);
  const isEmpty = day.open_count === 0;
  const availability = isEmpty ? 'no slots' : String(day.open_count) + ' open';
  const tone = isSelected
    ? 'border-grit-blue-strong bg-grit-blue-strong text-white'
    : 'border-line-strong bg-white text-ink hover:border-grit-blue-strong';
  return (
    <button
      type="button"
      role="radio"
      aria-checked={isSelected}
      aria-label={`${label.weekday} ${label.day} ${label.month}, ${availability}`}
      disabled={isEmpty}
      onClick={() => {
        props.onSelect(day.date);
      }}
      className={`flex min-w-0 flex-col items-center rounded-xl border py-2 transition disabled:cursor-not-allowed disabled:border-line disabled:bg-sand/60 disabled:text-muted ${tone}`}
    >
      <span className="text-[11px] font-medium uppercase opacity-80">{label.weekday}</span>
      <span className="font-display text-xl leading-tight font-semibold">{label.day}</span>
      <span className="text-[11px] font-semibold opacity-90">
        {isEmpty ? '–' : day.open_count}
        <span className="hidden sm:inline">{isEmpty ? '' : ' open'}</span>
      </span>
    </button>
  );
}

function WeekButton(
  props: Readonly<{ label: string; symbol: string; disabled: boolean; onClick: () => void }>,
): ReactElement {
  return (
    <button
      type="button"
      aria-label={props.label}
      disabled={props.disabled}
      onClick={props.onClick}
      className="flex size-9 items-center justify-center rounded-full border border-line-strong bg-white text-lg text-ink hover:border-grit-blue-strong disabled:opacity-35"
    >
      <span aria-hidden="true">{props.symbol}</span>
    </button>
  );
}

/** One week at a time, seven equal columns, arrows to move between weeks. */
export function DayStrip({ days, selected, onSelect }: Readonly<Props>): ReactElement {
  const startIndex = Math.max(
    0,
    days.findIndex((d) => d.date === selected),
  );
  const [page, setPage] = useState(Math.floor(startIndex / WEEK));
  const lastPage = Math.max(0, Math.ceil(days.length / WEEK) - 1);
  const week = days.slice(page * WEEK, page * WEEK + WEEK);
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold" aria-live="polite">
          {rangeLabel(week)}
        </p>
        <div className="flex gap-2">
          <WeekButton
            label="Previous week"
            symbol="‹"
            disabled={page === 0}
            onClick={() => {
              setPage(page - 1);
            }}
          />
          <WeekButton
            label="Next week"
            symbol="›"
            disabled={page >= lastPage}
            onClick={() => {
              setPage(page + 1);
            }}
          />
        </div>
      </div>
      <div role="radiogroup" aria-label="Pick a day" className="grid grid-cols-7 gap-1.5 sm:gap-2">
        {week.map((day) => (
          <DayCell
            key={day.date}
            day={day}
            isSelected={selected === day.date}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
