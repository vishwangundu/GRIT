import { Fragment, type ReactElement } from 'react';

import { Chip } from '@/components/ui/Chip';
import { Empty } from '@/components/ui/StateView';
import { useNow } from '@/hooks/use-now';
import { CHIP_LABELS } from '@/lib/labels';
import { formatRange, formatTime } from '@/lib/time';
import type { ScheduleItem } from '@/types/models';

interface Props {
  items: ScheduleItem[];
  isToday: boolean;
  selected: string | null;
  onOpen: (bookingId: string) => void;
}

function NowLine({ now }: Readonly<{ now: Date }>): ReactElement {
  return (
    <li
      aria-label={`Now, ${formatTime(now.toISOString())}`}
      className="flex items-center gap-2 py-1"
    >
      <span className="text-xs font-bold text-grit-red-strong">Now</span>
      <span className="h-0.5 flex-1 bg-grit-red" />
    </li>
  );
}

function Item({
  item,
  isSelected,
  onOpen,
}: Readonly<{
  item: ScheduleItem;
  isSelected: boolean;
  onOpen: (id: string) => void;
}>): ReactElement {
  const chip = CHIP_LABELS[item.chip];
  const content = (
    <>
      <span className="w-40 shrink-0 text-sm font-semibold">
        {formatRange(item.start_at, item.end_at)}
      </span>
      <span className="flex-1 text-sm">
        {item.student_name ?? <span className="text-muted">No student</span>}
        {item.badge_name ? <span className="text-muted"> · {item.badge_name}</span> : null}
      </span>
      <Chip tone={chip.tone}>{chip.label}</Chip>
    </>
  );
  const base =
    'flex w-full flex-wrap items-center gap-2 rounded-xl border border-line px-3 py-2 text-left';
  if (!item.booking_id) {
    return <li className={`${base} bg-white`}>{content}</li>;
  }
  const bookingId = item.booking_id;
  return (
    <li>
      <button
        type="button"
        aria-pressed={isSelected}
        onClick={() => {
          onOpen(bookingId);
        }}
        className={`${base} bg-white hover:border-grit-blue-strong aria-pressed:border-grit-blue-strong aria-pressed:bg-select aria-pressed:ring-1 aria-pressed:ring-grit-blue-strong`}
      >
        {content}
      </button>
    </li>
  );
}

export function ScheduleList({ items, isToday, selected, onOpen }: Readonly<Props>): ReactElement {
  const now = useNow();
  if (items.length === 0)
    return <Empty>No slots on this day. Add availability to open some.</Empty>;
  const nowIndex = isToday ? items.findIndex((i) => new Date(i.start_at) > now) : -1;
  return (
    <ul className="flex flex-col gap-2">
      {items.map((item, index) => (
        <Fragment key={item.slot_id}>
          {index === nowIndex ? <NowLine now={now} /> : null}
          <Item item={item} isSelected={selected === item.booking_id} onOpen={onOpen} />
        </Fragment>
      ))}
      {isToday && nowIndex === -1 ? <NowLine now={now} /> : null}
    </ul>
  );
}
