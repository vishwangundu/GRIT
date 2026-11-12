import type { ReactElement } from 'react';

import { Card } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Chip';
import { formatDateTime } from '@/lib/time';
import type { Schedule } from '@/types/models';

interface Props {
  items: Schedule['to_record'];
  selected: string | null;
  onOpen: (bookingId: string) => void;
}

export function ResultsBanner({ items, selected, onOpen }: Readonly<Props>): ReactElement | null {
  if (items.length === 0) return null;
  return (
    <Card tone="danger" band={`Results to record (${String(items.length)})`}>
      <ul className="flex flex-col gap-1">
        {items.map((item) => (
          <li key={item.booking_id}>
            <button
              type="button"
              aria-pressed={selected === item.booking_id}
              onClick={() => {
                onOpen(item.booking_id);
              }}
              className="flex w-full flex-wrap items-center justify-between gap-2 rounded-lg border border-transparent px-3 py-2 text-left text-sm hover:bg-sand aria-pressed:border-grit-blue-strong aria-pressed:bg-select aria-pressed:ring-1 aria-pressed:ring-grit-blue-strong"
            >
              <span>
                <strong>{item.student_name}</strong> · {formatDateTime(item.start_at)}
              </span>
              <Chip tone={item.is_overdue ? 'danger' : 'warning'}>
                {item.is_overdue ? 'Result overdue' : 'Record result'}
              </Chip>
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
