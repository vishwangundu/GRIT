import type { ReactElement } from 'react';

import { Card } from '@/components/ui/Card';
import { Empty } from '@/components/ui/StateView';
import { stateLabel } from '@/lib/labels';
import { formatDateTime } from '@/lib/time';
import type { EventItem } from '@/types/models';

const REASONS: Record<string, string> = {
  student_booked: 'You booked',
  student_rescheduled: 'You rescheduled',
  student_cancelled: 'You cancelled',
  interviewer_cancelled: 'Interviewer cancelled',
  derived_at_read: 'Updated automatically',
  eligibility_recompute: 'Skills updated',
  outcome_pass: 'Result: Pass',
  outcome_fail: 'Result: Fail',
  outcome_retake_later: 'Result: Retake later',
  outcome_no_show: 'Result: Didn’t join',
  outcome_edit_undo: 'Result corrected',
  flag_raised: 'Review opened',
  flag_uphold: 'Review upheld',
  flag_dismiss: 'Review dismissed',
  admin_reassigned: 'Interviewer changed',
  seed_booking: 'Booked (demo data)',
};

function EventRow({
  event,
  isLatest,
}: Readonly<{ event: EventItem; isLatest: boolean }>): ReactElement {
  const reason = event.reason ? (REASONS[event.reason] ?? event.reason) : null;
  return (
    <li className="relative pb-4 pl-6 last:pb-0">
      <span
        aria-hidden="true"
        className={`absolute top-1.5 left-0 size-2.5 rounded-full ring-4 ring-white ${
          isLatest ? 'bg-grit-blue-strong' : 'bg-line-strong'
        }`}
      />
      <p className="text-sm font-semibold">{stateLabel(event.to_state)}</p>
      <p className="text-sm text-muted">
        {reason ? `${reason} · ` : ''}
        <time dateTime={event.created_at}>{formatDateTime(event.created_at)}</time>
      </p>
    </li>
  );
}

export function JourneyHistory({ events }: Readonly<{ events: EventItem[] }>): ReactElement {
  return (
    <Card title="Journey history">
      {events.length === 0 ? (
        <Empty>No activity yet.</Empty>
      ) : (
        <ol className="relative">
          <span aria-hidden="true" className="absolute top-2 bottom-2 left-[4.5px] w-px bg-line" />
          {events.map((event, index) => (
            <EventRow
              key={`${event.created_at}-${event.to_state}`}
              event={event}
              isLatest={index === 0}
            />
          ))}
        </ol>
      )}
    </Card>
  );
}
