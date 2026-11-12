import type { ReactElement } from 'react';

import { Card } from '@/components/ui/Card';
import { plural } from '@/lib/labels';
import { formatDateTime } from '@/lib/time';
import type { SlotsResponse } from '@/types/models';

type Current = NonNullable<SlotsResponse['current_booking']>;

function guidance(current: Current): string {
  if (current.can_change) {
    return `Pick a new time below. ${plural(current.reschedules_left, 'reschedule')} left.`;
  }
  if (current.reschedules_left === 0) return 'You’ve used both reschedules for this interview.';
  return 'Changes close 12 hours before your interview.';
}

export function RescheduleHeader({ current }: Readonly<{ current: Current }>): ReactElement {
  return (
    <Card tone={current.can_change ? 'info' : 'warning'} band="Your current interview">
      <p className="text-sm">
        Current interview: <strong>{formatDateTime(current.start_at)} IST</strong>
      </p>
      <p className="mt-1 text-sm">{guidance(current)}</p>
    </Card>
  );
}
