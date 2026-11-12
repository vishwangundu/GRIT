import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { formatTime } from '@/lib/time';
import type { BookingView } from '@/types/models';

export function JoinButton({ booking }: Readonly<{ booking: BookingView }>): ReactElement {
  if (booking.is_join_open && booking.meeting_link) {
    return (
      <ButtonLink href={booking.meeting_link} isExternal>
        Join interview
      </ButtonLink>
    );
  }
  return (
    <Button disabled title="The join link appears 10 minutes before the start">
      Join opens {formatTime(booking.join_opens_at)}
    </Button>
  );
}
