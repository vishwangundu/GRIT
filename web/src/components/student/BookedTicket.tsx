import type { ReactElement } from 'react';

import { PersonName } from '@/components/ui/Avatar';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { plural } from '@/lib/labels';
import { formatDate, formatRange } from '@/lib/time';
import type { BookingView, JourneyCard } from '@/types/models';

import { CancelBookingButton } from './CancelBookingButton';
import { JoinButton } from './JoinButton';

interface Props {
  journey: JourneyCard;
  booking: BookingView;
  isLive: boolean;
}

export function BookedTicket({ journey, booking, isLive }: Readonly<Props>): ReactElement {
  const canReschedule = booking.can_change && booking.reschedules_left > 0;
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="text-muted">Badge</dt>
        <dd className="font-semibold">{journey.badge.name}</dd>
        <dt className="text-muted">Date</dt>
        <dd className="font-semibold">{formatDate(booking.start_at)}</dd>
        <dt className="text-muted">Time</dt>
        <dd className="font-semibold">{formatRange(booking.start_at, booking.end_at)}</dd>
        <dt className="text-muted">Interviewer</dt>
        <dd>
          <PersonName name={booking.interviewer_name} />
        </dd>
        <dt className="text-muted">Where</dt>
        <dd className="font-semibold">Online (Google Meet)</dd>
      </dl>
      <div className="flex flex-wrap gap-2">
        <JoinButton booking={booking} />
        {isLive ? null : (
          <>
            {canReschedule ? (
              <ButtonLink href="/student/book" variant="secondary">
                Reschedule ({plural(booking.reschedules_left, 'change')} left)
              </ButtonLink>
            ) : (
              <span className="self-center text-sm text-muted">
                {booking.reschedules_left === 0
                  ? 'No reschedules left'
                  : 'Changes closed (under 12 h to go)'}
              </span>
            )}
            <CancelBookingButton canCancel={booking.can_change} />
          </>
        )}
      </div>
    </div>
  );
}
